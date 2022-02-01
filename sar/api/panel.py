import socket
import threading
import re
import random
from typing import List, Callable

from server import BaseHandler
from config import MAFIA_CONFIG


class State:
    INIT = -1
    MAIN_MENU = 0
    EXTERNAL_SERVERS = 1
    ADMIN_MENU = 2

    ACTIVE_STATES = [MAIN_MENU, EXTERNAL_SERVERS, ADMIN_MENU]

    def prev(self, state):
        if state in [self.EXTERNAL_SERVERS, self.ADMIN_MENU]:
            return self.MAIN_MENU
        return self.MAIN_MENU


class RoleNames:
    ADMIN = 'ADMIN'
    NORMAL = 'NORMAL'

    LIST = (ADMIN, NORMAL)


class Action:
    def __init__(
            self,
            pattern: str,
            handler: Callable,
            valid_states: List[str]
    ):
        self.pattern = pattern
        self.handler = handler
        self.matcher = re.compile(pattern)
        self.match_obj = None
        self.valid_states = valid_states

    def match(self, message: str):
        match = self.matcher.match(message)
        self.match_obj = match
        return match is not None

    def get_variables(self):
        if self.match_obj:
            return self.match_obj.groupdict()
        return None


BACK = Action(
    pattern=r'back',
    handler=lambda panel, **kwargs: panel.back(**kwargs),
    valid_states=[State.ADMIN_MENU, State.EXTERNAL_SERVERS]
)

SELECT = Action(
    pattern=r'select (?P<item_number>\d+)',
    handler=lambda item_number, panel, **kwargs: panel.select(
        item_number, **kwargs),
    valid_states=[State.ADMIN_MENU, State.EXTERNAL_SERVERS]
)

SET_FIREWALL_KIND = Action(
    pattern=r'activate (?P<firewall_kind>(whitelist|blacklist)) firewall',
    handler=lambda firewall_kind, panel, **kwargs: panel.set_firewall_kind(
        firewall_kind, **kwargs),
    valid_states=[State.ADMIN_MENU]
)

OPEN_PORT = Action(
    pattern=r'open port (?P<port_number>\d+)',
    handler=lambda port_number, panel, **kwargs: panel.open_port(
        port_number, **kwargs),
    valid_states=[State.ADMIN_MENU]
)

CLOSE_PORT = Action(
    pattern=r'close port (?P<port_number>\d+)',
    handler=lambda port_number, panel, **kwargs: panel.close_port(
        port_number, **kwargs),
    valid_states=[State.ADMIN_MENU]
)

STATUS = Action(
    pattern=r'status',
    handler=lambda panel, **kwargs: panel.status(**kwargs),
    valid_states=[
        State.INIT, State.MAIN_MENU,
        State.EXTERNAL_SERVERS, State.ADMIN_MENU
    ]
)

SET_PASSWORD = Action(
    pattern=r'set password (?P<password>.+)',
    handler=lambda password, panel, **kwargs: panel.set_password(
        password, **kwargs),
    valid_states=[State.INIT]
)


class Role:

    def __init__(self, name: str, actions: List[Action]):
        self.name = name
        self.actions = actions


ADMIN = Role(
    name=RoleNames.ADMIN,
    actions=[
        STATUS, BACK, SELECT, SET_PASSWORD,
        SET_FIREWALL_KIND, OPEN_PORT, CLOSE_PORT
    ]
)

NORMAL = Role(
    name=RoleNames.NORMAL,
    actions=[
        STATUS, BACK, SELECT
    ]
)

ROLES_DICT = {
    'ADMIN': ADMIN,
    'NORMAL': NORMAL,
}


class User:
    def __init__(
            self,
            socket: socket.socket,
            id: int,
            panel: 'SarPanel',
            role: Role = None,
            name: str = None,
            password: str = None
    ):
        self.socket = socket
        self.id = id
        self.panel = panel
        self.role = role
        self.name = name

    def send_message(self, message):
        self.socket.sendall(message.encode())

    def run_command(self, message):
        for action in self.role.actions:
            if action.match(message):
                if self.panel.current_state in action.valid_states:
                    variables = action.get_variables()
                    variables['panel'] = self.panel
                    variables['my_id'] = self.id
                    action.handler(**variables)
                    return
                else:
                    self.send_message('Invalid state to run your command!')
                    return
                pass
        self.send_message('Wrong command or no permission!')

    def is_alive(self):
        try:
            self.socket.sendall("heartbeat".encode())
        except Exception as e:
            print(e)
            return False
        else:
            return True


class SarPanel(BaseHandler):
    def __init__(self, config: dict):
        self.current_state = State.START
        self.ready = False
        self.users: List[User] = []
        self.next_id = 1
        self.killed_player_id = None
        self.lock = threading.Lock()
        self.active_players = []
        self.finished = False

    def _get_user(self, user_id: int):
        for user in self.users:
            if user.id == user_id:
                return user
        return None

    def _get_admin(self):
        for user in self.users:
            if user.role == ADMIN:
                return user
        return None

    def _get_player_by_role(self, role: Role):
        players = []
        for player in self.active_players:
            if player.role == role:
                players.append(player)
        return players

    def is_sar_ready(self):
        admin = self._get_admin()
        return bool(admin and admin.password)

    def _add_user(self, user):
        if self.is_sar_ready():
            self.users.append(user)
            self.active_players.append(user)
            user.role = ROLES_DICT[RoleNames.NORMAL]
            user.send_message("Connected to SAR Server!")
        elif not self.users:
            self.users.append(user)
            self.active_players.append(user)
            user.role = ROLES_DICT[RoleNames.ADMIN]
            user.send_message("Connected, You are admin!")
        else:
            user.send_message("SAR Server not ready! Please try again later.")
            user.socket.close()

    def handle(self, client: socket.socket, *args, **kwargs):
        user = User(socket=client, id=self.next_id, panel=self, name='')

        self.next_id += 1
        self._add_user(user)

        while True:
            try:
                message = client.recv(2048)
                print("message received", message)
                if message:
                    command = message.decode()
                    user.run_command(command)
                else:
                    print(f'user {user.id} disconnected')
                    self.remove_user(user)
            except Exception as e:
                print(e)
                print(f'user {user.id} disconnected')
                self.remove_user(user)

    def remove_user(self, user):
        self.users.remove(user)

    def back(self, **kwargs):
        pass

    def status(self, **kwargs):
        user = self._get_user(kwargs.get('my_id'))
        pass

    def select(self, user_id, **kwargs):
        pass

    def set_firewall_kind(self, firewall_kind, **kwargs):
        pass

    def open_port(self, port_number, **kwargs):
        pass

    def close_port(self, port_number, **kwargs):
        pass

    def set_password(self, password, **kwargs):
        pass

    def inform_all(self, message, ignore_list=None):
        if not ignore_list:
            ignore_list = []
        for user in self.users:
            if user.id not in ignore_list:
                user.send_message(message)


sar_panel = SarPanel(config=MAFIA_CONFIG)
