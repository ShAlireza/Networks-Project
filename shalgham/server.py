import socket
from _thread import *

class User:
  def __init__(self, username, password):
    self.username = username
    self.password = password


def handle_inbox(c, user):
    while True:
        list_of_usernames = list(users.keys())
        list_of_usernames.remove(user.username)
        users_list_text = ''.join(e + '\n' for e in list_of_usernames)
        c.send(users_list_text.encode())
        data = c.recv(1024)

def handle_login(c):
    while True:
        c.send('1. Sign Up\n2. Login\n3. Exit\n'.encode())
        data = c.recv(1024)
        if str(data.decode('ascii')) == '1':
            c.send('Please enter your username.'.encode())
            data = c.recv(1024)
            username = str(data.decode('ascii'))
            while username in users.keys():
                c.send('This username is already existed or invalid. Please enter anotherone.'.encode())
                data = c.recv(1024)
                username = str(data.decode('ascii'))

            c.send('Please enter your password.'.encode())
            data = c.recv(1024)
            password = str(data.decode('ascii'))
            users.update({username : User(username, password)})
            
            
        elif str(data.decode('ascii')) == '2':
            c.send('Please enter your username.'.encode())
            data = c.recv(1024)
            username = str(data.decode('ascii'))
            c.send('Please enter your password.'.encode())
            data = c.recv(1024)
            password = str(data.decode('ascii'))
            if(username in users.keys() and users.get(username).password == password):
                start_new_thread(handle_inbox, (c,users.get(username)))
                break
            else:
                c.send('Incorrect username or password.\n'.encode())
                continue
        else:
            print('incorrect input\n')
         

users = {}
host = ""
port = 12343
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((host, port))
print("socket binded to port", port)
s.listen(1000)
print("socket is listening")

while True:
    c, addr = s.accept()
    print('Connected to :', addr[0], ':', addr[1])
    start_new_thread(handle_login, (c,))
        
