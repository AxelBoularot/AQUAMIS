#!/usr/bin/env python3

import requests
import json
import time
import sys

PHONE_IP = sys.argv[1] if len(sys.argv) > 1 else "192.168.1.100"
PHONE_PORT = 5050
OUTPUT_FILE = "sensor_data.json"
UPDATE_INTERVAL = 0.02

try:
    url = f"http://{PHONE_IP}:{PHONE_PORT}/get?gyrX&gyrY&gyrZ"
    response = requests.get(url, timeout=2)
    
    if response.status_code == 200:
        data = response.json()
        buffers = list(data.get('buffer', {}).keys())
    else:
        exit(1)
        
except Exception as e:
    exit(1)

accumulated_angles = {
    "roll": 0.0,
    "pitch": 0.0,
    "yaw": 0.0
}

last_print_time = time.time()

try:
    while True:
        try:
            response = requests.get(url, timeout=1)
            
            if response.status_code == 200:
                data = response.json()
                buffers = data.get('buffer', {})
                
                gyrX = buffers.get('gyrX', {}).get('buffer', [0])[-1] if buffers.get('gyrX', {}).get('buffer') else 0
                gyrY = buffers.get('gyrY', {}).get('buffer', [0])[-1] if buffers.get('gyrY', {}).get('buffer') else 0
                gyrZ = buffers.get('gyrZ', {}).get('buffer', [0])[-1] if buffers.get('gyrZ', {}).get('buffer') else 0
                
                accumulated_angles['yaw'] += gyrX * 57.2958 * UPDATE_INTERVAL
                accumulated_angles['pitch'] += gyrY * 57.2958 * UPDATE_INTERVAL
                accumulated_angles['roll'] += gyrZ * 57.2958 * UPDATE_INTERVAL
                
                for key in accumulated_angles:
                    while accumulated_angles[key] > 180:
                        accumulated_angles[key] -= 360
                    while accumulated_angles[key] < -180:
                        accumulated_angles[key] += 360
                
                with open(OUTPUT_FILE, "w") as f:
                    json.dump(accumulated_angles, f)
                
                current_time = time.time()
                if current_time - last_print_time >= 1.0:
                    last_print_time = current_time
                    
        except requests.exceptions.RequestException:
            pass
        except Exception as e:
            pass
        
        time.sleep(UPDATE_INTERVAL)

except KeyboardInterrupt:
    pass
