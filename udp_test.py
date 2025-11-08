import socket
import sys

# --- Configuration ---
HOST = "0.0.0.0"  # Listen on all available network interfaces
PORT = 8080       # The port your phone app is sending data to
# -------------------

print("--- UDP Test Server ---")
print(f"Attempting to listen on {HOST}:{PORT}")

# Create a UDP socket
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((HOST, PORT))
    print(f"Successfully listening on port {PORT}.")
    print("Please start sending data from your phone app now.")
    print("Press Ctrl+C to stop.")
except Exception as e:
    print(f"\n!!! ERROR: Could not bind to port {PORT}. Is another program using it?")
    print(f"    Details: {e}")
    sys.exit()

# Loop to receive data
try:
    while True:
        try:
            data, addr = s.recvfrom(1024)  # Buffer size is 1024 bytes
            print(f"Received {len(data)} bytes from {addr}: {data}")
        except Exception as e:
            print(f"Error while receiving data: {e}")
            break
except KeyboardInterrupt:
    print("\n--- Server stopped by user. ---")
finally:
    s.close()
    print("Socket closed.")
