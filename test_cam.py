import cv2
import socket
import threading
from time import sleep

HOST = '0.0.0.0'
VIDEO_PORT = 9999
RESOLUTION = (320, 240)
FPS = 60
JPEG_QUALITY = 30

class VideoStreamer:
    def __init__(self, host=HOST, port=VIDEO_PORT, resolution=RESOLUTION, fps=FPS, quality=JPEG_QUALITY):
        self.host = host
        self.port = port
        self.resolution = resolution
        self.fps = fps
        self.quality = quality
        self.sock = None
        self.client = None
        self.cap = None
        self.running = True

    def start_camera(self):
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)
        return self.cap.isOpened()

    def setup_socket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.listen(1)
        print(f"En attente de connexion vidéo sur {self.host}:{self.port}...")
        self.client, addr = self.sock.accept()
        print(f"Client connecté pour la vidéo : {addr}")

    def send_frames(self):
        frame_interval = 1.0 / self.fps
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                break
            _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, self.quality])
            data = buf.tobytes()
            size = len(data).to_bytes(4, 'big')
            try:
                self.client.sendall(size + data)
            except:
                break
            sleep(frame_interval)

    def run(self):
        if not self.start_camera():
            print("❌ Impossible d'initialiser la caméra")
            return
        print("✅ Caméra démarrée")
        self.setup_socket()
        try:
            self.send_frames()
        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()

    def cleanup(self):
        self.running = False
        if self.cap:
            self.cap.release()
        if self.client:
            self.client.close()
        if self.sock:
            self.sock.close()
        print("🛑 Serveur vidéo arrêté")

if __name__ == "__main__":
    streamer = VideoStreamer()
    streamer.run()
