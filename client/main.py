import threading
import socket
import sys


class Client:
    def __init__(self, server_host: str, server_port: int):
        self.server_host = server_host
        self.server_port = server_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.server_host, self.server_port))

    def start(self):
        thread = threading.Thread(target=self.read)
        thread.start()
        while True:
            command = input()
            if command == 'exit':
                self.socket.close()
                break
            self.socket.sendall(command.encode())
            # response = self.socket.recv(2048)
            # print(response)

    def read(self):
        while True:
            try:
                message = self.socket.recv(2048).decode()
                if message:
                    if(len(message.split('///')) > 2 and message.split('///')[0] == 'RECEIVE_ONLINE_MESSAGE'):
                        self.socket.sendall(message.encode('ascii'))
                    elif(len(message.split('///')) > 1 and message.split('///')[0] == 'SHOW_ONLINE_MESSAGE'):
                        print(''.join(i for i in message.split('///')[1:]))
                    else:
                        print(message)
                    pass
                else:
                    break
            except Exception as e:
                print(e)
                break


client = Client(server_host=sys.argv[1], server_port=int(sys.argv[2]))

client.start()
