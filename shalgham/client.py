import socket
from _thread import *
import threading


def handle_receive_message():
    while True:
        data = s.recv(1024)
        print(str(data.decode('ascii')))
 
def handle_send_message():
    while True:
        message = input()
        s.send(message.encode('ascii'))

 
host = '127.0.0.1'
port = 12343
 
s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.connect((host,port))

receive_thread = threading.Thread(target=handle_receive_message)
receive_thread.start()

send_thread = threading.Thread(target=handle_send_message)
send_thread.start()

 