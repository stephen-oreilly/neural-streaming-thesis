#!/usr/bin/env python3
"""PC-side checker for the nRF7002DK sine-wave UDP stream.

Packet: <uint32 seq><uint32 first_sample><uint16 samples[N]>, little-endian.
Expected signal: round(32768 + 20000*sin(2*pi*i/300)), i = global sample index.

Usage:  python receiver.py [--port 5005] [--plot]
Stop with Ctrl+C (prints a summary; --plot then shows the first received samples).
"""
import argparse
import socket
import struct
import time

import numpy as np

PERIOD = 300
AMP = 20000
OFFSET = 32768
TOLERANCE = 2  # LSBs; firmware uses float sinf, we use float64
HDR = struct.Struct("<II")
TABLE = np.round(OFFSET + AMP * np.sin(2 * np.pi * np.arange(PERIOD) / PERIOD)).astype(np.int32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=5005)
    ap.add_argument("--plot", action="store_true", help="plot first ~900 samples on exit")
    args = ap.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 * 1024 * 1024)
    sock.bind(("0.0.0.0", args.port))
    sock.settimeout(1.0)
    print(f"Listening on UDP :{args.port} ... (Ctrl+C to stop)")

    expected_seq = None
    received = lost = reordered = bad_samples = total_samples = bytes_rx = 0
    win_pkts = win_bytes = 0
    win_start = time.monotonic()
    t0 = None
    kept = []

    try:
        while True:
            try:
                data, addr = sock.recvfrom(4096)
            except socket.timeout:
                if received:
                    print("... no packets for 1 s")
                continue

            if t0 is None:
                t0 = time.monotonic()
                print(f"First packet from {addr[0]}:{addr[1]}, {len(data)} bytes")

            if len(data) < HDR.size + 2 or (len(data) - HDR.size) % 2:
                print(f"Malformed packet ({len(data)} bytes)")
                continue

            seq, first = HDR.unpack_from(data)
            samples = np.frombuffer(data, dtype="<u2", offset=HDR.size).astype(np.int32)
            n = samples.size

            received += 1
            bytes_rx += len(data)
            win_pkts += 1
            win_bytes += len(data)
            total_samples += n

            if expected_seq is None or seq == expected_seq:
                expected_seq = seq + 1
            elif seq > expected_seq:
                lost += seq - expected_seq
                expected_seq = seq + 1
            else:  # late / reordered (or duplicate)
                reordered += 1
                if lost > 0:
                    lost -= 1

            expected = TABLE[(first + np.arange(n)) % PERIOD]
            bad_samples += int(np.count_nonzero(np.abs(samples - expected) > TOLERANCE))

            if args.plot and len(kept) < 900:
                kept.extend(samples.tolist())

            now = time.monotonic()
            if now - win_start >= 1.0:
                dt = now - win_start
                print(f"{win_pkts / dt:7.1f} pkt/s  {win_bytes * 8 / dt / 1e3:7.1f} kbit/s  "
                      f"total rx={received} lost={lost} reordered={reordered} bad_samples={bad_samples}")
                win_pkts = win_bytes = 0
                win_start = now
    except KeyboardInterrupt:
        pass

    print("\n--- summary ---")
    sent_est = received + lost
    print(f"packets received : {received}")
    print(f"packets lost     : {lost}" + (f" ({100 * lost / sent_est:.3f}%)" if sent_est else ""))
    print(f"reordered/dup    : {reordered}")
    print(f"samples checked  : {total_samples}, mismatches: {bad_samples}")
    if t0 is not None:
        dur = time.monotonic() - t0
        print(f"duration {dur:.1f}s, mean goodput {bytes_rx * 8 / dur / 1e3:.1f} kbit/s (incl. headers)")

    if args.plot and kept:
        import matplotlib.pyplot as plt
        plt.plot(kept)
        plt.title("Received samples (first ~900)")
        plt.xlabel("sample")
        plt.ylabel("uint16 value")
        plt.show()


if __name__ == "__main__":
    main()
