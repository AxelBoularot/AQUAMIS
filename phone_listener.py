"""
AQUAMIS - Phone Sensor Listener
================================
Lit les données du gyroscope depuis l'application Phyphox
et les écrit dans sensor_data.json pour l'interface AQUAMIS.

Configuration requise:
- Application Phyphox sur le téléphone
- Expérience "Gyroscope" lancée
- "Allow remote access" activé dans Phyphox
- Téléphone et PC sur le même réseau WiFi

Auteur: AMIS Team
Date: Novembre 2025
"""

import requests
import json
import time

# ============================================================
# CONFIGURATION
# ============================================================

# IP du téléphone (affichée dans Phyphox sous "Allow remote access")
PHONE_IP = "192.168.1.157"
PHONE_PORT = 8080

# Fichier de sortie pour l'interface AQUAMIS
OUTPUT_FILE = "sensor_data.json"

# Intervalle entre chaque lecture (en secondes)
UPDATE_INTERVAL = 0.05  # 50ms = 20Hz

# ============================================================
# FONCTIONS
# ============================================================

def get_phyphox_data():
    """
    Récupère les données du gyroscope depuis Phyphox via HTTP.
    Retourne les données JSON ou None en cas d'erreur.
    """
    try:
        url = f"http://{PHONE_IP}:{PHONE_PORT}/get?gyrX&gyrY&gyrZ"
        response = requests.get(url, timeout=1)
        
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None


def extract_orientation(phyphox_data, accumulated_angles, dt):
    """
    Extrait et intègre les données du gyroscope.
    
    Le gyroscope donne des vitesses angulaires (rad/s).
    On les intègre pour obtenir des angles absolus (degrés).
    
    Args:
        phyphox_data: Données JSON de Phyphox
        accumulated_angles: Dict des angles accumulés (modifié in-place)
        dt: Intervalle de temps depuis la dernière lecture (secondes)
    
    Returns:
        Dict avec roll, pitch, yaw en degrés, ou None si erreur
    """
    if not phyphox_data or 'buffer' not in phyphox_data:
        return None
    
    buffers = phyphox_data['buffer']
    
    try:
        # Extraire les vitesses angulaires (rad/s)
        gyrX = buffers.get('gyrX', {}).get('buffer', [0])[-1]
        gyrY = buffers.get('gyrY', {}).get('buffer', [0])[-1]
        gyrZ = buffers.get('gyrZ', {}).get('buffer', [0])[-1]
        
        # Intégrer: angle = angle_précédent + vitesse × temps
        # Conversion rad/s → deg: × 57.2958
        accumulated_angles['roll'] += gyrX * 57.2958 * dt
        accumulated_angles['pitch'] += gyrY * 57.2958 * dt
        accumulated_angles['yaw'] += gyrZ * 57.2958 * dt
        
        # Normaliser les angles entre -180° et +180°
        for key in accumulated_angles:
            while accumulated_angles[key] > 180:
                accumulated_angles[key] -= 360
            while accumulated_angles[key] < -180:
                accumulated_angles[key] += 360
        
        return {
            "roll": accumulated_angles['roll'],
            "pitch": accumulated_angles['pitch'],
            "yaw": accumulated_angles['yaw']
        }
    except:
        return None


def test_connection():
    """Test la connexion à Phyphox et affiche les buffers disponibles."""
    print("Test de connexion à Phyphox...")
    data = get_phyphox_data()
    
    if data and 'buffer' in data:
        buffers = list(data['buffer'].keys())
        print(f"✅ Connexion réussie!")
        print(f"   Buffers disponibles: {buffers}")
        return True
    else:
        print(f"❌ Impossible de se connecter à Phyphox")
        print(f"\nVérifiez:")
        print(f"  - Phyphox est ouvert avec l'expérience 'Gyroscope'")
        print(f"  - L'expérience est démarrée (bouton play)")
        print(f"  - 'Allow remote access' est activé")
        print(f"  - L'adresse est correcte: http://{PHONE_IP}:{PHONE_PORT}")
        return False


def run_listener():
    """
    Boucle principale du listener.
    Lit continuellement les données de Phyphox et les écrit dans sensor_data.json.
    """
    print("=" * 60)
    print("  AQUAMIS - PHONE SENSOR LISTENER")
    print("=" * 60)
    print(f"\nConnexion à Phyphox sur {PHONE_IP}:{PHONE_PORT}")
    print("\nConfiguration requise:")
    print("  1. Phyphox ouvert sur 'Gyroscope'")
    print("  2. Expérience DÉMARRÉE (bouton play ▶️)")
    print("  3. 'Allow remote access' ACTIVÉ (menu ⋮)")
    print("\nAppuyez sur Ctrl+C pour arrêter")
    print("=" * 60)
    print()
    
    # Initialisation
    last_data = {"roll": 0, "pitch": 0, "yaw": 0}
    accumulated_angles = {"roll": 0, "pitch": 0, "yaw": 0}
    
    try:
        while True:
            phyphox_data = get_phyphox_data()
            
            if phyphox_data:
                orientation = extract_orientation(phyphox_data, accumulated_angles, UPDATE_INTERVAL)
                
                if orientation:
                    last_data = orientation
                    
                    # Écrire dans le fichier JSON
                    with open(OUTPUT_FILE, "w") as f:
                        json.dump(last_data, f)
                    
                    # Afficher les valeurs en temps réel
                    print(f"\rYaw={last_data['yaw']:8.2f}°  "
                          f"Pitch={last_data['pitch']:8.2f}°  "
                          f"Roll={last_data['roll']:8.2f}°", end="")
            
            time.sleep(UPDATE_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n")
        print("=" * 60)
        print("  Listener arrêté")
        print("=" * 60)
    except Exception as e:
        print(f"\n\n❌ ERREUR: {e}")


# ============================================================
# POINT D'ENTRÉE
# ============================================================

if __name__ == '__main__':
    # Test de connexion avant de démarrer
    if test_connection():
        print()
        run_listener()
    else:
        print("\nImpossible de démarrer le listener.")
        print("Corrigez les problèmes ci-dessus et réessayez.")
