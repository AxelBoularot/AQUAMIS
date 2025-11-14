#!/usr/bin/env python3
"""
AQUAMIS - Phone Sensor Listener
Lit les données du gyroscope depuis Phyphox et les écrit dans sensor_data.json
"""

import requests
import json
import time
import sys

# ============================================================
# CONFIGURATION
# ============================================================
# L'IP peut être passée en argument
PHONE_IP = sys.argv[1] if len(sys.argv) > 1 else "192.168.1.157"
PHONE_PORT = 5050                # Port de Phyphox (changé de 8080 car la caméra l'utilise)
OUTPUT_FILE = "data/sensor_data.json" # Fichier pour l'interface AQUAMIS
UPDATE_INTERVAL = 0.05           # 50ms entre chaque lecture

# ============================================================
# PROGRAMME PRINCIPAL
# ============================================================

print("=" * 60)
print("  AQUAMIS - PHONE SENSOR LISTENER")
print("=" * 60)
print()
print(f"Configuration:")
print(f"  - IP téléphone : {PHONE_IP}")
print(f"  - Port         : {PHONE_PORT}")
print(f"  - Sortie       : {OUTPUT_FILE}")
print()

# Test de connexion
print("Test de connexion à Phyphox...")
try:
    url = f"http://{PHONE_IP}:{PHONE_PORT}/get?gyrX&gyrY&gyrZ"
    response = requests.get(url, timeout=2)
    
    if response.status_code == 200:
        data = response.json()
        buffers = list(data.get('buffer', {}).keys())
        print(f"✅ Connexion réussie!")
        print(f"   Buffers détectés: {buffers}")
    else:
        print(f"❌ Erreur HTTP {response.status_code}")
        exit(1)
        
except Exception as e:
    print(f"❌ Impossible de se connecter: {e}")
    print()
    print("Vérifiez que:")
    print("  1. Phyphox est ouvert avec 'Gyroscope'")
    print("  2. L'expérience est DÉMARRÉE (bouton play)")
    print("  3. 'Allow remote access' est ACTIVÉ")
    print(f"  4. L'adresse est correcte: http://{PHONE_IP}:{PHONE_PORT}")
    exit(1)

print()
print("=" * 60)
print("  LISTENER ACTIF")
print("=" * 60)
print("Bougez votre téléphone - Les angles s'accumulent")
print("Appuyez sur Ctrl+C pour arrêter")
print()

# Angles cumulés (intégration des vitesses angulaires)
accumulated_angles = {
    "roll": 0.0,
    "pitch": 0.0,
    "yaw": 0.0
}

# Boucle principale
try:
    while True:
        try:
            # Récupérer les données du gyroscope
            response = requests.get(url, timeout=1)
            
            if response.status_code == 200:
                data = response.json()
                buffers = data.get('buffer', {})
                
                # Extraire les vitesses angulaires (rad/s)
                gyrX = buffers.get('gyrX', {}).get('buffer', [0])[-1] if buffers.get('gyrX', {}).get('buffer') else 0
                gyrY = buffers.get('gyrY', {}).get('buffer', [0])[-1] if buffers.get('gyrY', {}).get('buffer') else 0
                gyrZ = buffers.get('gyrZ', {}).get('buffer', [0])[-1] if buffers.get('gyrZ', {}).get('buffer') else 0
                
                # Intégrer les vitesses pour obtenir les angles
                # angle = angle_précédent + vitesse_angulaire * temps * conversion_rad_vers_deg
                # NOTE: roll et yaw sont inversés pour correspondre à l'orientation d'AQUAMIS
                accumulated_angles['yaw'] += gyrX * 57.2958 * UPDATE_INTERVAL    # Inversé
                accumulated_angles['pitch'] += gyrY * 57.2958 * UPDATE_INTERVAL
                accumulated_angles['roll'] += gyrZ * 57.2958 * UPDATE_INTERVAL   # Inversé
                
                # Normaliser les angles entre -180° et +180°
                for key in accumulated_angles:
                    while accumulated_angles[key] > 180:
                        accumulated_angles[key] -= 360
                    while accumulated_angles[key] < -180:
                        accumulated_angles[key] += 360
                
                # Écrire dans le fichier JSON pour l'interface
                with open(OUTPUT_FILE, "w") as f:
                    json.dump(accumulated_angles, f)
                
                # Afficher les valeurs en temps réel
                print(f"\rYaw={accumulated_angles['yaw']:7.1f}°  "
                    f"Pitch={accumulated_angles['pitch']:7.1f}°  "
                    f"Roll={accumulated_angles['roll']:7.1f}°  ", 
                    end="", flush=True)
                    
        except requests.exceptions.RequestException:
            # Ignorer les erreurs de connexion temporaires
            pass
        except Exception as e:
            print(f"\nErreur: {e}")
        
        # Attendre avant la prochaine lecture
        time.sleep(UPDATE_INTERVAL)

except KeyboardInterrupt:
    print("\n")
    print("=" * 60)
    print("  Listener arrêté")
    print("=" * 60)
    print(f"\nDernières valeurs:")
    print(f"  Yaw   = {accumulated_angles['yaw']:.2f}°")
    print(f"  Pitch = {accumulated_angles['pitch']:.2f}°")
    print(f"  Roll  = {accumulated_angles['roll']:.2f}°")
