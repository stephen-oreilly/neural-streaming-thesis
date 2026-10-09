"""Export losslessly re-centered Intan AC amplifier samples to a raw binary file.

Reads a traditional, single-file .rhs recording in 128-sample blocks, retaining
only the requested AC amplifier channels. The binary output is little-endian
signed int16, time-interleaved: [t0/ch0, t0/ch1, ..., t1/ch0, t1/ch1, ...].

The conversion is exact and reversible: int16_sample = uint16_ADC - 32768.
No Intan headers, timestamps, stimulation words or floating-point conversions
are included in the .bin output. A companion .json records its interpretation.

Requires inspect_rhs.py and Intan's importrhsutilities.py beside this script,
and NumPy in the selected Python environment.

Example:
    python extract_rhs.py --file "C:\\Data\\recording.rhs" --channels 0-7 --duration 5
    python extract_rhs.py --file "C:\\Data\\recording.rhs" --channels A-000,A-001 --start 2 --duration 1

Alternatively, paste the recording path into RHS_FILE below and run in VS Code.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re

import numpy as np

from inspect_rhs import SCRIPT_DIR, inspect_file


# =========================== USER CONFIGURATION =============================
RHS_FILE = r"C:\Users\steph\OneDrive\Documents\College\Year_5.1\Thesis\Neural-Data\Codebase\Scripts\baseline_250721_135507.rhs"                # Paste the full .rhs path here (or use --file).
CHANNELS = "0-7"              # Header indices, e.g. 0-7, or names, e.g. A-000,A-001.
START_SECONDS = 0.0           # Nominal position in the recording.
DURATION_SECONDS = 5.0        # How much data to extract.
OUTPUT_DIRECTORY = r""       # Leave empty for <project>/Data/extracted.
OUTPUT_NAME = ""              # Leave empty to generate a descriptive filename.
# ===========================================================================

# For the recommended Neural-Data/Scripts/extraction/ layout, use the project
# root's Data/extracted directory. If moved elsewhere, use a local folder.
if SCRIPT_DIR.name.lower() == "extraction" and SCRIPT_DIR.parent.name.lower() == "scripts":
    DEFAULT_OUTPUT_DIRECTORY = SCRIPT_DIR.parent.parent / "Data" / "extracted"
else:
    DEFAULT_OUTPUT_DIRECTORY = SCRIPT_DIR / "extracted"

FLASH_CAPACITY_BYTES = 8 * 1024 * 1024  # Nominal MX25R64 capacity, not usable partition size.
SAMPLES_PER_BYTE = 2  # Exactly two bytes per signed 16-bit sample.


def parse_channels(spec: str, available: list[dict]) -> list[int]:
    """Return unique channel indices, in the user-requested output order."""
    if spec.strip().lower() == "all":
        return list(range(len(available)))

    lookup = {}
    for i, channel in enumerate(available):
        for key in ("native_channel_name", "custom_channel_name"):
            name = channel[key]
            if name in lookup and lookup[name] != i:
                lookup[name] = None  # Ambiguous custom name: refuse to guess.
            else:
                lookup[name] = i

    result = []
    for token in spec.split(","):
        token = token.strip()
        match = re.fullmatch(r"(\d+)-(\d+)", token)
        if match:
            first, last = map(int, match.groups())
            if first > last:
                raise ValueError(f"Channel range must be ascending: {token}")
            values = range(first, last + 1)
        elif re.fullmatch(r"\d+", token):
            values = [int(token)]
        elif token in lookup:
            if lookup[token] is None:
                raise ValueError(f"Ambiguous channel name: {token}")
            values = [lookup[token]]
        else:
            raise ValueError(f"Unknown channel '{token}'. Run inspect_rhs.py to list names/indices.")

        for index in values:
            if index < 0 or index >= len(available):
                raise ValueError(f"Channel index {index} is outside 0..{len(available)-1}.")
            if index in result:
                raise ValueError(f"Channel index {index} was selected twice.")
            result.append(index)

    if not result:
        raise ValueError("Select at least one amplifier channel.")
    return result


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def extract(
    source: str | Path,
    channels: str,
    start_seconds: float,
    duration_seconds: float,
    output_directory: str | Path,
    output_name: str = "",
    overwrite: bool = False,
) -> tuple[Path, Path]:
    """Stream selected RHS amplifier samples to .bin + .json; never load full RHS."""
    info = inspect_file(source)
    header = info["header"]
    if info["trailing_bytes"]:
        raise ValueError("RHS contains an incomplete block; refusing to extract ambiguous data.")
    if info["num_blocks"] == 0:
        raise ValueError("No data blocks found. Header-only RHS + separate .dat files are not supported.")

    indices = parse_channels(channels, header["amplifier_channels"])
    sample_rate = info["sample_rate_hz"]
    if not all(math.isfinite(x) for x in (start_seconds, duration_seconds)):
        raise ValueError("Start and duration must be finite numbers.")
    if start_seconds < 0 or duration_seconds <= 0:
        raise ValueError("Start must be >= 0 and duration must be > 0.")

    first_sample = round(start_seconds * sample_rate)
    count = round(duration_seconds * sample_rate)
    final_sample = first_sample + count  # exclusive
    if count < 1:
        raise ValueError("Duration is shorter than one recording sample.")
    if first_sample >= info["total_samples_per_channel"] or final_sample > info["total_samples_per_channel"]:
        raise ValueError(
            f"Requested sample range [{first_sample}, {final_sample}) exceeds recording "
            f"length ({info['total_samples_per_channel']} samples/channel, "
            f"{info['duration_seconds']:.6f} s)."
        )

    out_dir = Path(output_directory).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    if output_name:
        stem = Path(output_name).name
        if stem.lower().endswith((".bin", ".json")):
            stem = Path(stem).stem
        if stem in ("", ".", ".."):
            raise ValueError("Invalid output name.")
    else:
        stem = f"{info['path'].stem}_{len(indices)}ch_{first_sample}start_{count}samples"

    binary_path = out_dir / f"{stem}.bin"
    metadata_path = out_dir / f"{stem}.json"
    temporary_path = out_dir / f"{stem}.bin.part"
    if not overwrite and any(p.exists() for p in (binary_path, metadata_path, temporary_path)):
        raise FileExistsError("An output file already exists. Choose another name or pass --overwrite.")

    expected_bytes = count * len(indices) * SAMPLES_PER_BYTE
    if expected_bytes > FLASH_CAPACITY_BYTES:
        print(f"WARNING: {expected_bytes:,} bytes exceeds nominal 8 MiB external flash capacity.")
    print(f"Extracting {len(indices)} channels × {count:,} samples = {expected_bytes:,} bytes")
    print("Output: little-endian int16, time-interleaved, no header")

    block_samples = info["samples_per_block"]
    num_amplifiers = header["num_amplifier_channels"]
    amp_bytes = num_amplifiers * block_samples * SAMPLES_PER_BYTE
    timestamp_bytes = block_samples * 4
    first_block = first_sample // block_samples
    last_block = (final_sample - 1) // block_samples

    digest = hashlib.sha256()
    bytes_written = 0
    first_timestamp = None
    last_timestamp = None
    discontinuities = 0

    try:
        with info["path"].open("rb") as source_handle, temporary_path.open("wb") as output_handle:
            for block in range(first_block, last_block + 1):
                start = info["data_offset"] + block * info["block_bytes"]
                source_handle.seek(start)
                ts_raw = source_handle.read(timestamp_bytes)
                amp_raw = source_handle.read(amp_bytes)
                if len(ts_raw) != timestamp_bytes or len(amp_raw) != amp_bytes:
                    raise IOError(f"Unexpected EOF in data block {block}.")

                block_first_sample = block * block_samples
                local_first = max(0, first_sample - block_first_sample)
                local_end = min(block_samples, final_sample - block_first_sample)
                timestamps = np.frombuffer(ts_raw, dtype="<i4")[local_first:local_end]
                if last_timestamp is not None and int(timestamps[0]) != last_timestamp + 1:
                    discontinuities += 1
                discontinuities += int(np.count_nonzero(np.diff(timestamps.astype(np.int64)) != 1))
                if first_timestamp is None:
                    first_timestamp = int(timestamps[0])
                last_timestamp = int(timestamps[-1])

                # RHS: all 128 samples of each channel are consecutive.
                raw = np.frombuffer(amp_raw, dtype="<u2").reshape(num_amplifiers, block_samples)
                selected = raw[indices, local_first:local_end]
                # Exact, reversible integer conversion; no uV scale or float rounding.
                signed = (selected.astype(np.int32) - 32768).astype("<i2")
                chunk = signed.T.tobytes(order="C")  # Time × selected-channel order.
                output_handle.write(chunk)
                digest.update(chunk)
                bytes_written += len(chunk)

        if bytes_written != expected_bytes or temporary_path.stat().st_size != expected_bytes:
            raise IOError(f"Expected {expected_bytes} bytes but wrote {bytes_written}.")
        if sha256_file(temporary_path) != digest.hexdigest():
            raise IOError("Read-back SHA-256 differs from written data; output is not verified.")

        # Commit only after the complete output has passed length/hash verification.
        os.replace(temporary_path, binary_path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()

    manifest = {
        "source_file": info["path"].name,
        "source_file_size_bytes": info["file_size"],
        "source_rhs_version": header["version"],
        "source_header_size_bytes": info["data_offset"],
        "source_data_block_size_bytes": info["block_bytes"],
        "sample_rate_hz": sample_rate,
        "source_start_sample_zero_based": first_sample,
        "source_first_timestamp": first_timestamp,
        "source_last_timestamp": last_timestamp,
        "timestamp_discontinuities": discontinuities,
        "start_seconds_nominal": first_sample / sample_rate,
        "duration_seconds_nominal": count / sample_rate,
        "number_of_channels": len(indices),
        "channels": [
            {
                "source_header_index_zero_based": index,
                "native_name": header["amplifier_channels"][index]["native_channel_name"],
                "custom_name": header["amplifier_channels"][index]["custom_channel_name"],
            }
            for index in indices
        ],
        "samples_per_channel": count,
        "sample_encoding": "signed_int16_little_endian",
        "sample_conversion_from_rhs": "signed_sample = original_uint16_adc_code - 32768",
        "layout": "time_interleaved; channels follow the order in the channels list",
        "includes_rhs_header": False,
        "includes_timestamps": False,
        "includes_stimulation": False,
        "data_size_bytes": expected_bytes,
        "binary_file": binary_path.name,
        "sha256": digest.hexdigest(),
    }
    metadata_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Binary:   {binary_path}")
    print(f"Metadata: {metadata_path}")
    print(f"Read-back SHA-256 verified: {digest.hexdigest()}")
    if discontinuities:
        print(f"WARNING: {discontinuities} timestamp discontinuity/ies in the selected interval.")
    return binary_path, metadata_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", default=RHS_FILE, help="Input traditional .rhs file")
    parser.add_argument("--channels", default=CHANNELS, help="e.g. 0-7, 0,2,5, A-000,A-001, or all")
    parser.add_argument("--start", type=float, default=START_SECONDS, help="Start offset in seconds (default: 0)")
    parser.add_argument("--duration", type=float, default=DURATION_SECONDS, help="Extraction duration in seconds (default: 5)")
    parser.add_argument("--output-dir", default=OUTPUT_DIRECTORY or str(DEFAULT_OUTPUT_DIRECTORY))
    parser.add_argument("--name", default=OUTPUT_NAME, help="Optional output stem (without extension)")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing output pair")
    args = parser.parse_args()
    extract(args.file, args.channels, args.start, args.duration, args.output_dir, args.name, args.overwrite)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, ImportError) as exc:
        raise SystemExit(f"ERROR: {exc}") from exc
