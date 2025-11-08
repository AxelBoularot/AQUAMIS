import socket
import threading
import struct
import math

# --- Configuration ---
DEFAULT_PORT = 8080
# Smoothing factor to reduce jitter. Lower value = smoother but more lag.
# Good values are between 0.1 (smooth) and 0.5 (responsive).
SMOOTHING_FACTOR = 0.15
# -------------------

def lerp(start, end, t):
    """Linear interpolation"""
    return start + (end - start) * t

class PhoneSensorServer(threading.Thread):
    """
    A server that listens for UDP packets from a phone sensor streaming app
    and makes the data available to the main application.
    """
    def __init__(self, host="0.0.0.0", port=DEFAULT_PORT):
        super().__init__()
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        # Smoothed data
        self.smoothed_data = {
            "roll": 0,
            "pitch": 0,
            "yaw": 0
        }
        self.data_lock = threading.Lock()
        self.daemon = True

    def run(self):
        """Starts the UDP server and listens for data."""
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.server_socket.bind((self.host, self.port))
            print(f"[Phone Sensor] Listening on {self.host}:{self.port}")
        except Exception as e:
            print(f"[Phone Sensor] Error binding to port {self.port}: {e}")
            self.running = False
            return

        while self.running:
            try:
                data, addr = self.server_socket.recvfrom(1024)
                self.parse_data(data)
            except Exception as e:
                if self.running:
                    print(f"[Phone Sensor] Error during data processing: {e}")

    def parse_data(self, data_bytes):
        """
        Parses the incoming binary data from Sensor UDP app.
        It sends 3 floats for orientation: Azimuth (Yaw), Pitch, Roll.
        """
        if len(data_bytes) < 12:
            return

        try:
            # Sensor UDP sends orientation as 3 floats: Azimuth, Pitch, Roll
            # We unpack them directly. The format is little-endian ('<').
            azimuth, pitch, roll = struct.unpack_from('<fff', data_bytes, 0)

            with self.data_lock:
                # Apply smoothing (lerp) to the new values
                self.smoothed_data["yaw"] = lerp(self.smoothed_data["yaw"], azimuth, SMOOTHING_FACTOR)
                # We might need to invert pitch or roll depending on the phone's coordinate system
                self.smoothed_data["pitch"] = lerp(self.smoothed_data["pitch"], -pitch, SMOOTHING_FACTOR)
                self.smoothed_data["roll"] = lerp(self.smoothed_data["roll"], -roll, SMOOTHING_FACTOR)

            # Optional: print the smoothed, corrected values
            # print(f"[Phone Sensor] Smoothed: Yaw={self.smoothed_data['yaw']:.2f}, Pitch={self.smoothed_data['pitch']:.2f}, Roll={self.smoothed_data['roll']:.2f}")

        except struct.error:
            # This might happen if the packet format is unexpected.
            pass
        except Exception as e:
            print(f"[Phone Sensor] Error parsing binary data: {e}")

    def get_latest_data(self):
        """Returns the most recent, smoothed sensor data."""
        with self.data_lock:
            # Convert to degrees for the cube display
            return {
                "yaw": math.degrees(self.smoothed_data["yaw"]),
                "pitch": math.degrees(self.smoothed_data["pitch"]),
                "roll": math.degrees(self.smoothed_data["roll"]),
            }

    def stop(self):
        """Stops the server."""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        print("[Phone Sensor] Server stopped.")

if __name__ == '__main__':
    # Example of how to run the server for testing purposes
    sensor_server = PhoneSensorServer()
    sensor_server.start()
    print("Phone sensor server started. Press Ctrl+C to stop.")
    
    try:
        while True:
            import time
            time.sleep(1)
            latest_data = sensor_server.get_latest_data()
            print(f"Latest data: Yaw={latest_data['yaw']:.2f}, Pitch={latest_data['pitch']:.2f}, Roll={latest_data['roll']:.2f}")
    except KeyboardInterrupt:
        sensor_server.stop()
        sensor_server.join()
        print("Server shut down gracefully.")
