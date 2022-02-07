from .server import BaseHandler
import socket
import threading
import re
from typing import List, Callable
from .video_sender import send_video


class ShalghamHandler(BaseHandler):
    movies = [
        'cool_baby',
        'poor_rabbit',
    ]

    def __init__(self, config: dict = None):
        self.ready = False
        self.killed_player_id = None
        self.finished = False
        self.config = config if config else {}
        self.user = None

    def handle(self, client: socket.socket, *args, **kwargs):
        while True:
            try:
                client.sendall(self.get_menu().encode())
                message = client.recv(2048)
                print("message received", message)
                if message:
                    command = message.decode()
                    if command == "back":
                        client.sendall("##exit##".encode())
                    if self.is_select_command(command):
                        self.show_video(client, int(command.split(" ")[1]))
            except Exception as e:
                pass

    def get_menu(self):
        message = ""
        i = 1
        for movie in self.movies:
            message += str(i) + ". " + movie + "\n"
            i += 1
        message += "back"
        return message

    def is_select_command(self, command):
        command_parts = command.split(" ")
        if len(command_parts) != 2:
            return False
        if command_parts[0] != "select":
            return False
        if int(command_parts[1]) > len(self.movies):
            return False
        if int(command_parts[1]) < 1:
            return False
        return True

    def show_video(self, client: socket.socket, file_index):
        client.sendall("video_at: 9010".encode())
        movie = self.movies[file_index-1]
        stop_threads = False

        t1 = threading.Thread(target=send_video, args=(movie, 9010, lambda: stop_threads,))
        t1.start()
        while True:
            message = client.recv(2048).decode()
            if message == "stop":
                stop_threads = True
                print("must stop")
                break
