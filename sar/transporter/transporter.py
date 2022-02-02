import socket
import threading


class TransporterClient:
    def __init__(self, src_socket: socket.socket,
                 server_host: str, server_port: int, firewall):
        self.src_socket = src_socket
        self.server_host = server_host
        self.server_port = server_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.server_host, self.server_port))
        self.firewall = firewall

    def start(self):
        thread = threading.Thread(target=self.read)
        thread.start()
        while True:
            data = self.src_socket.recv(2048)
            if self.firewall:
                data = self.firewall.apply(
                    data=data,
                    source_ip=self.src_socket.getpeername()[0],
                    source_port=self.src_socket.getpeername()[1]
                )
            if data:
                self.socket.sendall(data)

    def read(self):
        while True:
            try:
                data = self.socket.recv(2048)
                if data:
                    self.src_socket.sendall(data)
                    print(data.decode())
                    if data == '##exit##':
                        self.socket.close()
                        break
                    pass
                else:
                    break
            except Exception as e:
                print(e)
                break


class Transporter:

    def __init__(self, src_socket: socket.socket, des_port,
                 des_ip='127.0.0.1', firewall=None):
        self.src_socket = src_socket
        self.des_ip = des_ip
        self.des_port = des_port
        self.des_socket = None

    def start(self):
        t_client = TransporterClient(
            src_socket=self.src_socket,
            server_host=self.des_ip,
            server_port=self.des_port,
            firewall=self.firewall
        )
        t_client.start()
