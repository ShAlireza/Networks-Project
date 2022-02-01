import socket
import threading
from typing import List


class BaseHandler:

    def handle(self, client: socket.socket, *args, **kwargs):
        raise NotImplementedError


class SarServer:

    def __init__(
            self,
            host: str = '127.0.0.1',
            port: int = 8000,
            handler: BaseHandler = None,
            handler_class: type(BaseHandler) = None,
            handler_kwargs: dict = None,
    ):
        self.host = host
        self.port = port
        self.handler_class = handler_class
        self.handler = handler

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.socket.bind((self.host, self.port))

        self.socket.listen(10)

    def start(self):
        while True:
            print('Ready to accept connections...')
            client, address = self.socket.accept()
            print(f'Connection accepted from {address}')
            handler = self.handler if not self.handler_class else \
                self.handler_class()

            thread = threading.Thread(
                target=self.handler.handle, args=(client,)
            )
            thread.start()
