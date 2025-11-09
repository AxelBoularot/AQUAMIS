import cv2
import socket
import serial
import json
import threading
from time import sleep

PORT = "COM5"  # ⚠️ Vérifie ton port série !
BAUDRATE = 115200
ser = None  # Le port série sera initialisé après activation de la caméra

class VideoStream:
    def __init__(self, resolution=(320, 240), fps=60):
        self.resolution = resolution
        self.fps = fps
        self.camera = None
        
    def start(self):
        self.camera = cv2.VideoCapture(0)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
        self.camera.set(cv2.CAP_PROP_FPS, self.fps)
        self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        return self.camera.isOpened()
        
    def read(self):
        return self.camera.read()
        
    def stop(self):
        if self.camera:
            self.camera.release()

class SocketManager:
    def __init__(self, host='192.168.1.108', video_port=9999, data_port=8888):
        self.host = host
        self.video_port = video_port
        self.data_port = data_port
        self.video_socket = None
        self.data_socket = None
        self.video_client = None
        self.data_client = None
        self.running = True

    def setup_sockets(self):
        # Configuration des sockets
        self.video_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Options des sockets
        for sock in [self.video_socket, self.data_socket]:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
        
        # Bind
        self.video_socket.bind((self.host, self.video_port))
        self.data_socket.bind((self.host, self.data_port))
        
        # Listen
        self.video_socket.listen(1)
        self.data_socket.listen(1)
        
        print(f"En attente sur {self.host}:")
        print(f"Vidéo: port {self.video_port}")
        print(f"Données: port {self.data_port}")

    def accept_connections(self):
        self.video_client, addr1 = self.video_socket.accept()
        print(f"Client vidéo connecté: {addr1}")
        
        self.data_client, addr2 = self.data_socket.accept()
        print(f"Client données connecté: {addr2}")

    def close(self):
        self.running = False
        for sock in [self.video_client, self.data_client, 
                     self.video_socket, self.data_socket]:
            if sock:
                sock.close()

class StreamServer:
    def __init__(self, resolution=(320, 240), fps=60):
        self.video_stream = VideoStream(resolution, fps)
        self.socket_manager = SocketManager()
        self.running = True
    
    def envoyer_json(self, data):
        """Envoie un JSON à Arduino."""
        json_str = json.dumps(data) + "\n"
        ser.write(json_str.encode('utf-8'))

    def lire_json(self):
        """Lit un JSON valide depuis Arduino sans bloquer."""
        try:
            ligne = ser.readline().decode('utf-8').strip()
            if ligne.startswith("{"):  # Vérifier si c'est un JSON valide
                return json.loads(ligne)
            elif ligne:
                print(f"🔸 Message ignoré : {ligne}")  # Pour le débogage
        except json.JSONDecodeError:
            print(f"⚠️ Erreur JSON : {ligne}")
        return None
    
    def handle_data(self):
        while self.running:
            try:
                size = int.from_bytes(self.socket_manager.data_client.recv(4), byteorder='big')
                data = self.socket_manager.data_client.recv(size).decode('utf-8')
                message = json.loads(data)
                print(f"Reçu: {message}")
                self.envoyer_json(message)
                
                # Traitement et réponse
                response = self.lire_json()
                response_json = json.dumps(response).encode('utf-8')
                size_bytes = len(response_json).to_bytes(4, byteorder='big')
                self.socket_manager.data_client.send(size_bytes + response_json)
            except:
                break
                
    def send_frame(self, frame):
        try:
            _, encoded = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 30])
            data = encoded.tobytes()
            size = len(data).to_bytes(4, byteorder='big')
            self.socket_manager.video_client.sendall(size + data)
            return True
        except:
            return False

    def run(self):
        try:
            # Initialisation des sockets
            self.socket_manager.setup_sockets()

            # Démarrage de la caméra
            if not self.video_stream.start():
                raise Exception("Impossible d'initialiser la caméra")

            print("✅ Caméra active, démarrage du port série...")

            # Initialisation du port série après activation de la caméra
            """global ser
            ser = serial.Serial(PORT, BAUDRATE, timeout=0.1)"""

            # Accepter les connexions
            self.socket_manager.accept_connections()

            # Démarrer le thread de gestion des données
            data_thread = threading.Thread(target=self.handle_data)
            data_thread.start()

            # Boucle principale vidéo
            frame_time = 1.0 / self.video_stream.fps
            while self.running:
                ret, frame = self.video_stream.read()
                if not ret or not self.send_frame(frame):
                    break
                sleep(frame_time)  # Contrôle du framerate

        except Exception as e:
            print(f"Erreur: {e}")
        """finally:
            self.cleanup()"""

    def cleanup(self):
        self.running = False
        self.video_stream.stop()
        self.socket_manager.close()

if __name__ == "__main__":
    server = StreamServer()
    try:
        server.run()
    except KeyboardInterrupt:
        print("\nArrêt du serveur")
        