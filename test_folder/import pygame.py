import cv2
import socket
import json
import threading
import numpy as np
from time import time
import pygame

class SocketClient:
    def __init__(self, host='192.168.0.13', video_port=9999, data_port=8888):
        self.host = host
        self.video_port = video_port
        self.data_port = data_port
        self.video_socket = None
        self.data_socket = None
        self.running = True

    def connect(self):
        # Création et configuration des sockets
        self.video_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        for sock in [self.video_socket, self.data_socket]:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)

        print(f"Connexion à {self.host}...")
        try:
            self.video_socket.connect((self.host, self.video_port))
            self.data_socket.connect((self.host, self.data_port))
            print("Connecté!")
        except Exception as e:
            print(f"Erreur de connexion: {e}")
            self.running = False

    def close(self):
        self.running = False
        if self.video_socket:
            self.video_socket.close()
        if self.data_socket:
            self.data_socket.close()

class VideoReceiver(threading.Thread):
    def __init__(self, socket_client):
        super().__init__()
        self.socket_client = socket_client
        self.frame = None
        self.frame_lock = threading.Lock()
        self.running = True

    def run(self):
        while self.running and self.socket_client.running:
            frame = self.receive_frame()
            with self.frame_lock:
                self.frame = frame

    def receive_frame(self):
        try:
            # Réception de la taille
            size_data = self.socket_client.video_socket.recv(4)
            if not size_data:
                return None
            size = int.from_bytes(size_data, byteorder='big')
            if size == 0:
                return None

            # Réception des données
            data = b''
            while len(data) < size:
                packet = self.socket_client.video_socket.recv(size - len(data))
                if not packet:
                    return None
                data += packet

            # Décodage de l'image
            img_array = np.frombuffer(data, dtype=np.uint8)
            frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            return frame
        except:
            return None

class DataHandler(threading.Thread):
    def __init__(self, socket_client):
        super().__init__()
        self.socket_client = socket_client
        self.message_to_send = {"status": "running", "timestamp": time()}
        self.received_data = None
        self.data_lock = threading.Lock()
        self.running = True

    def run(self):
        while self.running and self.socket_client.running:
            try:
                # Envoi du message
                msg_json = json.dumps(self.message_to_send).encode('utf-8')
                size = len(msg_json).to_bytes(4, byteorder='big')
                self.socket_client.data_socket.sendall(size + msg_json)

                # Réception de la réponse
                size_data = self.socket_client.data_socket.recv(4)
                if not size_data:
                    continue
                size = int.from_bytes(size_data, byteorder='big')
                data = self.socket_client.data_socket.recv(size).decode('utf-8')
                response = json.loads(data)
                with self.data_lock:
                    self.received_data = response
            except Exception as e:
                with self.data_lock:
                    self.received_data = {"error": str(e)}
                continue

class StreamClient:
    def __init__(self, host='192.168.0.13'):
        self.socket_client = SocketClient(host)
        self.video_receiver = None
        self.data_handler = None
        self.running = True
        self.video_frame = None
        self.received_data = None
        self.message_to_send = ""
        self.message_lock = threading.Lock()

    def run(self):
        try:
            self.socket_client.connect()
            if not self.socket_client.running:
                print("Impossible de se connecter au serveur")

            # Initialisation de Pygame
            pygame.init()
            window_size = (800, 600)
            screen = pygame.display.set_mode(window_size)
            pygame.display.set_caption('Client Stream')

            font = pygame.font.SysFont(None, 24)
            clock = pygame.time.Clock()
            input_active = True
            input_box = pygame.Rect(10, window_size[1]-30, 140, 24)
            input_text = ''

            # Démarrage des threads si connecté
            if self.socket_client.running:
                self.video_receiver = VideoReceiver(self.socket_client)
                self.data_handler = DataHandler(self.socket_client)
                self.data_handler.message_to_send = {"status": "running", "timestamp": time()}
                self.data_handler.start()
                self.video_receiver.start()

            # Boucle principale
            while self.running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.KEYDOWN:
                        if input_active:
                            if event.key == pygame.K_RETURN:
                                with self.message_lock:
                                    try:
                                        json_message = json.loads(input_text)
                                        self.data_handler.message_to_send = json_message
                                    except:
                                        pass
                                input_text = ''
                            elif event.key == pygame.K_BACKSPACE:
                                input_text = input_text[:-1]
                            else:
                                input_text += event.unicode

                screen.fill((0,0,0))

                # Affichage de la vidéo
                if self.video_receiver and self.video_receiver.frame is not None:
                    with self.video_receiver.frame_lock:
                        frame = self.video_receiver.frame.copy()
                    if frame is not None:
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        frame = np.rot90(frame)
                        frame = pygame.surfarray.make_surface(frame)
                        screen.blit(frame, (0,0))

                # Affichage des données reçues
                if self.data_handler:
                    with self.data_handler.data_lock:
                        data_text = str(self.data_handler.received_data)
                    data_surface = font.render(f'Données reçues: {data_text}', True, (255, 255, 255))
                    screen.blit(data_surface, (10, window_size[1]-60))

                # Affichage de la zone de saisie
                txt_surface = font.render(input_text, True, (255, 255, 255))
                width = max(200, txt_surface.get_width()+10)
                input_box.w = width
                screen.blit(txt_surface, (input_box.x+5, input_box.y+5))
                pygame.draw.rect(screen, (255, 255, 255), input_box, 2)

                pygame.display.flip()
                clock.tick(30)

        except Exception as e:
            print(f"Erreur: {e}")
        finally:
            self.cleanup()

    def cleanup(self):
        self.running = False
        if self.socket_client.running:
            self.socket_client.close()
        if self.video_receiver:
            self.video_receiver.running = False
            self.video_receiver.join()
        if self.data_handler:
            self.data_handler.running = False
            self.data_handler.join()
        pygame.quit()

if __name__ == "__main__":
    test_envoie = {"servo_ballast":0,"servo_droit":0,"servo_gauche":0,"moteur_droit":0,"moteur_gauche":0}
    client = StreamClient()
    try:
        client.run()
    except KeyboardInterrupt:
        print("\nArrêt du client")


