import socket

hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)
print("Adresse IP locale :", local_ip)