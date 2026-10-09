"""Inspect a traditional (single-file) Intan RHS recording without loading its data.

Requires Intan's `importrhsutilities.py` beside this script (or importable in the
Python environment). See https://github.com/Intan-Technologies/load-rhs-notebook-python

Examples:
    python inspect_rhs.py --file "C:\\Data\\recording.rhs"
    python inspect_rhs.py --file "C:\\Data\\recording.rhs" --save-header

Alternatively, paste the path into RHS_FILE below and run the script in VS Code.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from pprint import pprint

from importrhsutilities import get_bytes_per_data_block, read_header


# =========================== USER CONFIGURATION =============================
# Paste the path to your .rhs file between the quotes. Keep the r prefix for
# Windows paths. Leave empty if supplying --file on the command line.
RHS_FILE = r""
# ===========================================================================

SCRIPT_DIR = Path(__file__).resolve().parent


def resolve_rhs_path(filename: str | Path) -> Path:
    """Resolve a user-supplied RHS path. Relative paths use the current directory."""
    text = str(filename).strip().strip('"').strip("'")
    if not text:
        raise ValueError("Set RHS_FILE at the top of the script or pass --file PATH.")
    path = Path(text).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"RHS file not found: {path}")
    if path.suffix.lower() != ".rhs":
        raise ValueError(f"Expected a .rhs file, got: {path.name}")
    return path


def inspect_file(filename: str | Path) -> dict:
    """Read just the header and calculate recording dimensions from file size.

    Returns a dictionary. A nonzero trailing_bytes count means the file does
    not contain a whole number of complete traditional-RHS blocks.
    """
    path = resolve_rhs_path(filename)
    file_size = path.stat().st_size

    with path.open("rb") as handle:
        header = read_header(handle)  # Intan's official header parser.
        data_offset = handle.tell()

    block_bytes = int(get_bytes_per_data_block(header))
    if block_bytes <= 0 or data_offset > file_size:
        raise ValueError("Invalid RHS header or calculated data-block length.")

    data_bytes = file_size - data_offset
    blocks, trailing_bytes = divmod(data_bytes, block_bytes)
    samples_per_block = int(header["num_samples_per_data_block"])
    total_samples = blocks * samples_per_block
    sample_rate = float(header["sample_rate"])

    return {
        "path": path,
        "header": header,
        "file_size": file_size,
        "data_offset": data_offset,
        "block_bytes": block_bytes,
        "data_bytes": data_bytes,
        "num_blocks": blocks,
        "trailing_bytes": trailing_bytes,
        "samples_per_block": samples_per_block,
        "total_samples_per_channel": total_samples,
        "sample_rate_hz": sample_rate,
        "duration_seconds": total_samples / sample_rate,
    }


def print_summary(info: dict) -> None:
    """Print recording dimensions and channels in file/storage order."""
    header = info["header"]
    version = header["version"]
    print("\n=== INTAN RHS RECORDING ===")
    print(f"File:                     {info['path']}")
    print(f"RHS version:              {version['major']}.{version['minor']}")
    print(f"File size:                {info['file_size']:,} bytes")
    print(f"Header size / data start: {info['data_offset']:,} bytes")
    print(f"Sampling frequency:       {info['sample_rate_hz']:g} Hz")
    print(f"Amplifier channels:       {header['num_amplifier_channels']}")
    print(f"Samples per data block:   {info['samples_per_block']}")
    print(f"Bytes per data block:     {info['block_bytes']:,}")
    print(f"Complete blocks:          {info['num_blocks']:,}")
    print(f"Samples per channel:      {info['total_samples_per_channel']:,}")
    print(f"Nominal duration:         {info['duration_seconds']:.6f} seconds")
    print(f"DC amplifier data saved:  {bool(header['dc_amplifier_data_saved'])}")
    print(f"Trailing bytes:           {info['trailing_bytes']}")
    if info["trailing_bytes"]:
        print("WARNING: File has an incomplete final data block. Do not extract it.")
    if not info["num_blocks"]:
        print("NOTE: This file has no complete traditional-RHS data blocks.")
        print("      It may be a header-only file for a separate .dat recording.")

    print("\n=== ENABLED AMPLIFIER CHANNELS (0-based file order) ===")
    print(f"{'Index':>5}  {'Name':<12} {'Port':<9} {'Stream':>6} {'Chip':>5} {'Impedance (ohm)':>18}")
    for index, channel in enumerate(header["amplifier_channels"]):
        print(
            f"{index:5d}  "
            f"{channel['native_channel_name']:<12} "
            f"{channel['port_name']:<9} "
            f"{channel['board_stream']:>6} "
            f"{channel['chip_channel']:>5} "
            f"{channel['electrode_impedance_magnitude']:>18.2f}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", default=RHS_FILE, help="Path to traditional .rhs recording")
    parser.add_argument(
        "--save-header", nargs="?", const="Header-structure.txt", metavar="PATH",
        help="Also save the complete parsed header; default: beside this script",
    )
    args = parser.parse_args()

    info = inspect_file(args.file)
    print_summary(info)

    if args.save_header is not None:
        output = Path(args.save_header).expanduser()
        if not output.is_absolute():
            output = SCRIPT_DIR / output
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", encoding="utf-8") as handle:
            pprint(info["header"], stream=handle, sort_dicts=False)
            handle.write(f"\nHeader size: {info['data_offset']} bytes\n")
        print(f"\nFull header saved to: {output.resolve()}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, ImportError) as exc:
        raise SystemExit(f"ERROR: {exc}") from exc
