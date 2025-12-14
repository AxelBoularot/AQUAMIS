import cv2
import socket
import json
import threading
import numpy as np
from time import time
import pygame

class SocketClient:
    def __init__(self, host='192.168.1.108', video_port=9999, data_port=8888):
        self.host = host
        self.video_port = video_port
        self.data_port = data_port
        self.video_socket = None
        self.data_socket = None
        self.running = True

    def connect(self):
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
            size_data = self.socket_client.video_socket.recv(4)
            if not size_data:
                return None
            size = int.from_bytes(size_data, byteorder='big')
            if size == 0:
                return None

            data = b''
            while len(data) < size:
                packet = self.socket_client.video_socket.recv(size - len(data))
                if not packet:
                    return None
                data += packet

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
                msg_json = json.dumps(self.message_to_send).encode('utf-8')
                size = len(msg_json).to_bytes(4, byteorder='big')
                self.socket_client.data_socket.sendall(size + msg_json)

                size = int.from_bytes(size_data, byteorder='big')
                data = self.socket_client.data_socket.recv(size).decode('utf-8')
                response = json.loads(data)
                with self.data_lock:
                    self.received_data = response
            except Exception as e:
                with self.data_lock:
                    self.received_data = {"error": str(e)}
                continue