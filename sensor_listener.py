import socket
import struct
import json
import time

# --- Configuration ---
HOST = "0.0.0.0"
PORT = 8080
OUTPUT_FILE = "sensor_data.json"
# -------------------

def run_server():
    """
    Listens for UDP packets from a sensor app, parses the orientation data,
    and writes it to a JSON file.
    """
    print("--- Sensor Listener ---")
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind((HOST, PORT))
        print(f"Listening for sensor data on port {PORT}...")
    except Exception as e:
        print(f"!!! ERROR: Could not bind to port {PORT}. Is another program (like a previous script) still using it?")
        print(f"    Details: {e}")
        return

    latest_data = {"roll": 0, "pitch": 0, "yaw": 0}

    try:
        while True:
            try:
                data, addr = s.recvfrom(1024)
                
                # Sensor UDP sends orientation as 3 floats: Azimuth, Pitch, Roll
                if len(data) >= 12:
                    azimuth, pitch, roll = struct.unpack_from('<fff', data, 0)
                    
                    # Convert to degrees and assign
                    latest_data["yaw"] = azimuth * 180 / 3.14159
                    latest_data["pitch"] = -pitch * 180 / 3.14159 # Invert for intuitive movement
                    latest_data["roll"] = -roll * 180 / 3.14159  # Invert for intuitive movement
                    
                    # Write to the JSON file
                    with open(OUTPUT_FILE, "w") as f:
                        json.dump(latest_data, f)
                        
                    print(f"Updated data: Yaw={latest_data['yaw']:.1f}, Pitch={latest_data['pitch']:.1f}, Roll={latest_data['roll']:.1f}", end="\r")

            except struct.error:
                # Ignore packets that don't have the correct float format
                continue
            except Exception as e:
                print(f"\nAn error occurred: {e}")
                time.sleep(1)

    except KeyboardInterrupt:
        print("\n--- Server stopped. ---")
    finally:
        s.close()
        print("Socket closed.")

if __name__ == '__main__':
    run_server()
