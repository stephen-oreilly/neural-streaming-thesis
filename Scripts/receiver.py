
import socket
import time
import numpy as np
import matplotlib.pyplot as plt

PORT = 5000
RECORD_DURATION = 10  # seconds
DISPLAY_SAMPLES = 2048

# Create UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", PORT))
sock.settimeout(0.1)

print(f"Listening on UDP port {PORT}...")
print("Waiting for first packet...")

received_data = []
packet_count = 0
byte_count = 0

try:
    # Wait indefinitely for first packet
    while True:
        try:
            data, sender = sock.recvfrom(65535)
            break
        except socket.timeout:
            continue

    # Start recording timer
    start_time = time.monotonic()

    received_data.append(data)
    packet_count += 1
    byte_count += len(data)

    print(f"First packet received from {sender}.")
    print(f"Recording for {RECORD_DURATION} seconds...")

    # Receive packets for specified duration
    while time.monotonic() - start_time < RECORD_DURATION:
        try:
            data, sender = sock.recvfrom(65535)

            received_data.append(data)
            packet_count += 1
            byte_count += len(data)

        except socket.timeout:
            continue

except KeyboardInterrupt:
    print("\nRecording interrupted.")

finally:
    sock.close()

# Calculate reception statistics
if packet_count > 0:
    elapsed = time.monotonic() - start_time

    print("\nRecording complete.")
    print(f"Duration: {elapsed:.2f} s")
    print(f"Packets received: {packet_count}")
    print(f"Bytes received: {byte_count}")
    print(f"Average goodput: {byte_count * 8 / elapsed / 1e6:.3f} Mbps")

    # Combine received packets
    raw_data = b"".join(received_data)

    # Interpret bytes as signed 16-bit samples
    samples = np.frombuffer(raw_data, dtype="<i2")

    print("First 20 received samples:")
    print(samples[:20])

    # Save samples
    np.save("received_samples.npy", samples)
    print(f"Saved {len(samples)} samples to received_samples.npy")

    

    # Plot first DISPLAY_SAMPLES samples
    plot_samples = samples[:DISPLAY_SAMPLES]

    plt.figure(figsize=(12, 5))
    plt.plot(plot_samples)

    plt.xlabel("Sample index")
    plt.ylabel("Amplitude")
    plt.title("Received UDP Samples")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

else:
    print("No packets received.")
