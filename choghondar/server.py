import socket
from _thread import *


class Message:
    def __init__(self, text, sender):
        self.text = text
        self.sender = sender

    def __repr__(self):
        return '{sender: ' + str(self.sender) + ', text: ' + str(self.text) + '}'


class Chat:
    def __init__(self, other_user):
        self.other_user = other_user
        self.unread = 0
        self.messages = []

    def add_message(self, text, sender):
        self.messages.append(Message(text, sender))
        if(sender == self.other_user):
            self.unread += 1

    def get_messages(self, number):
        self.unread = 0
        if(len(self.messages) >= number):
            return self.messages[-number:]
        else:
            return self.messages

    def read_unreads(self):
        self.unread = 0

    def __repr__(self):
        return '{other_user: ' + str(self.other_user) + ', messages: ' + str(self.messages) + '}'


class User:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.chats = [Chat(other.username) for other in users.values()]

    def __eq__(self, other):
        return self.username == other.username

    def __repr__(self):
        return '{username: ' + str(self.username) + ', password: ' + str(self.password) + ', chats: ' + str(self.chats) + '}'


def handle_send_online_chat(user, other_user, message):
    if other_user in online_users.keys():
        online_users.get(other_user).send(
            ('RECEIVE_ONLINE_MESSAGE///' + str(user) + '///' + message).encode())


def handle_receive_online_chat(c, message, user_chat):
    c.send(('SHOW_ONLINE_MESSAGE///' + message).encode())
    user_chat.read_unreads()


def handle_chat(c, user, other_user):
    for i in users.get(user).chats:
        if (i.other_user == other_user):
            user_chat = i
    for i in users.get(other_user).chats:
        if (i.other_user == user):
            other_user_chat = i

    selected_messages = user_chat.get_messages(5)
    chats_text = ''.join(str(e.sender) + ': ' +
                         str(e.text) + '\n' for e in selected_messages)
    c.send(chats_text.encode())

    while True:
        data = c.recv(1024)
        message = str(data.decode('ascii'))
        if(str(data.decode('ascii')) == 'bac'):
            c.send('##exit##'.encode())
            c.close()
            break
        if(len(message.split('///')) > 2 and message.split('///')[0] == 'RECEIVE_ONLINE_MESSAGE'):
            if(message.split('///')[1] == other_user):
                start_new_thread(handle_receive_online_chat,
                                 (c, message.split('///')[2], user_chat))
            continue
        elif(message == '/exit'):
            start_new_thread(handle_inbox, (c, users.get(user)))
            break
        if(len(message.split()) == 2 and message.split()[0] == '/load' and message.split()[1].isdigit()):
            selected_messages = user_chat.get_messages(int(message.split()[1]))
            chats_text = ''.join(str(e.sender) + ': ' + str(e.text) + '\n' if e.sender !=
                                 user else str(e.text) + '\n' for e in selected_messages)
            c.send(chats_text.encode())
        else:
            user_chat.add_message(message, user)
            users.get(user).chats.remove(user_chat)
            users.get(user).chats.insert(0, user_chat)

            other_user_chat.add_message(message, user)
            users.get(other_user).chats.remove(other_user_chat)
            users.get(other_user).chats.insert(0, other_user_chat)

            start_new_thread(handle_send_online_chat,
                             (user, other_user, '(' + user + ') ' + message))


def handle_inbox(c, user):
    list_of_chats = [i.other_user for i in user.chats]
    users_list_text = ''.join(e.other_user + '\n' if e.unread ==
                              0 else e.other_user + '(' + str(e.unread) + ')' + '\n' for e in user.chats)
    c.send(users_list_text.encode())

    data = c.recv(1024)
    other_user_username = str(data.decode('ascii'))

    while not other_user_username in list_of_chats or other_user_username == '0':
        if(str(data.decode('ascii')) == '##exit##'):
            c.send('##exit##'.encode())
            c.close()
            break
        if(len(str(data.decode('ascii')).split('///')) > 1 and str(data.decode('ascii')).split('///')[0] == 'RECEIVE_ONLINE_MESSAGE'):
            continue
        if(other_user_username == '0'):
            start_new_thread(handle_login, (c,))
            return
        data = c.recv(1024)
        other_user_username = str(data.decode('ascii'))

    start_new_thread(handle_chat, (c, user.username, other_user_username))


def handle_login(c):
    while True:
        c.send('1. Sign Up\n2. Login\n3. Exit\n'.encode())
        data = c.recv(1024)
        if(str(data.decode('ascii')) == 'back'):
            c.send('##exit##'.encode())
            c.close()
            break
        elif(len(str(data.decode('ascii')).split('///')) > 1 and str(data.decode('ascii')).split('///')[0] == 'RECEIVE_ONLINE_MESSAGE'):
            continue
        elif str(data.decode('ascii')) == '1':
            c.send('Please enter your username.'.encode())

            data = c.recv(1024)
            username = str(data.decode('ascii'))

            while username in users.keys():
                c.send(
                    'This username is already existed or invalid. Please enter anotherone.'.encode())
                data = c.recv(1024)
                username = str(data.decode('ascii'))

            c.send('Please enter your password.'.encode())

            data = c.recv(1024)
            password = str(data.decode('ascii'))

            new_user = User(username, password)
            for user in users.values():
                user.chats.append(Chat(new_user.username))
            users.update({username: new_user})

        elif str(data.decode('ascii')) == '2':
            c.send('Please enter your username.'.encode())

            data = c.recv(1024)
            username = str(data.decode('ascii'))

            c.send('Please enter your password.'.encode())

            data = c.recv(1024)
            password = str(data.decode('ascii'))

            if(username in users.keys() and users.get(username).password == password):
                start_new_thread(handle_inbox, (c, users.get(username)))
                online_users.update({username: c})
                break
            else:
                c.send('Incorrect username or password.\n'.encode())
                continue
        elif str(data.decode('ascii')) == '3':
            c.send('##exit##'.encode())
            c.close()
            break
        else:
            c.send('Incorrect input.\n'.encode())


users = {}
online_users = {}
host = ""
port = 9090
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((host, port))
print("socket binded to port", port)
s.listen(1000)
print("socket is listening")

while True:
    c, addr = s.accept()
    print('Connected to :', addr[0], ':', addr[1])
    start_new_thread(handle_login, (c,))
