import queue
from .server import BaseHandler
import socket
import threading


class ProxyHandler(BaseHandler):

    def __init__(self, config: dict = None):
        self.ready = False
        self.killed_player_id = None
        self.finished = False
        self.config = config if config else {}
        self.user = None
        self.q = queue.Queue()
        self.host = None
        self.client = None

    def handle(self, client: socket.socket, *args, **kwargs):
        self.client = client
        self.client.sendall("##where_to?##".encode())
        message = self.client.recv(2048).decode()
        port_num = 9090
        host_ip = '127.0.0.1'
        if message == "shalgham":
            port_num = 8080
        elif message != "choghondar":
            raise Exception
        self.client.sendall(f"connecting to {message}.".encode())
        self.host = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host.connect((host_ip, port_num))
        self.client.sendall("Connected.".encode())
        thread = threading.Thread(target=self.read)
        thread.start()
        while True:
            if not self.q.empty():
                value = self.q.get()
                print("Q Q:" + str(value))
                if value == "End of proxy.":
                    print("End of proxy.")
                    self.host.close()
                    return
            data = self.client.recv(2048)
            if data:
                self.host.sendall(data)

    def read(self):
        while True:
            try:
                data = self.host.recv(2048)
                if data:
                    print(data.decode())
                    if data.decode() == "##exit##":
                        self.client.sendall(data)
                        self.q.put("End of proxy.")
                        return
                    self.client.sendall(data)
                    pass
                else:
                    break
            except Exception as e:
                print(e)
                break


