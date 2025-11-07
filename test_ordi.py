import cv2
import socket
import numpy as np

SERVER_IP = '127.0.0.1'  # Remplace par l'IP de l'émetteur si besoin
VIDEO_PORT = 9999
WINDOW_NAME = 'Flux vidéo reçu'

def receive_stream(host=SERVER_IP, port=VIDEO_PORT):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    print(f"Connecté au serveur vidéo {host}:{port}")

    data_buffer = b''
    try:
        while True:
            # Lire la taille du prochain paquet (4 bytes)
            while len(data_buffer) < 4:
                packet = sock.recv(4096)
                if not packet:
                    return
                data_buffer += packet
            size = int.from_bytes(data_buffer[:4], 'big')
            data_buffer = data_buffer[4:]

            # Lire l'image elle-même
            while len(data_buffer) < size:
                packet = sock.recv(4096)
                if not packet:
                    return
                data_buffer += packet
            frame_data = data_buffer[:size]
            data_buffer = data_buffer[size:]

            # Décoder et afficher
            np_arr = np.frombuffer(frame_data, dtype=np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if frame is None:
                continue

            cv2.imshow(WINDOW_NAME, frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    except KeyboardInterrupt:
        pass
    finally:
        sock.close()
        cv2.destroyAllWindows()
        print("🛑 Réception vidéo arrêtée")

if __name__ == "__main__":
    receive_stream()
