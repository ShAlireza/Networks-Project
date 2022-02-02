import socket
import threading
import re
from typing import List, Callable

from .server import BaseHandler
from transporter.transporter import Transporter
from firewall.firewall import sar_firewall

from config import (
    CHOGHONDAR_IP,
    CHOGHONDAR_PORT,
    SHALGHAM_IP,
    SHALGHAM_PORT
)


class State:
    INIT = "INIT", "Init Connection, Please enter admin password"
    MAIN_MENU = ("MAIN_MENU",
                 "1) Connect to external servers\n2) Login as admin")
    EXTERNAL_SERVERS = ("EXTERNAL_SERVERS",
                        "1) shalgham\n2) choghondar")

    ADMIN_ASK_PASSWORD = ("ADMIN_ASK_PASSWORD",
                          "Please enter you password")
    ADMIN_MENU = ("ADMIN_MENU",
                  "You can config firewall")

    ACTIVE_STATES = [MAIN_MENU, EXTERNAL_SERVERS,
                     ADMIN_ASK_PASSWORD, ADMIN_MENU]

    @staticmethod
    def prev(state):
        if state in [State.EXTERNAL_SERVERS,
                     State.ADMIN_ASK_PASSWORD, State.ADMIN_MENU]:
            return State.MAIN_MENU
        return State.MAIN_MENU

    @staticmethod
    def state_string(state):
        return f"\n\n**********\t{state[0]}\t**********\n{state[1]}"


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
    valid_states=[State.MAIN_MENU, State.EXTERNAL_SERVERS]
)

SET_FIREWALL_KIND = Action(
    pattern=r'activate (?P<firewall_kind>(whitelist|blacklist)) firewall',
    handler=lambda firewall_kind, panel, **kwargs: panel.set_firewall_kind(
        firewall_kind, **kwargs),
    valid_states=[State.ADMIN_MENU]
)

OPEN_PORT = Action(
    pattern=r'open port (?P<src_ip>.+) (?P<src_port>\d+) '
    r'(?P<des_ip>.+) (?P<des_port>\d+)',
    handler=lambda src_ip, src_port, des_ip, des_port, panel, **kwargs:
    panel.open_port(
        src_ip, src_port, des_ip, des_port, **kwargs
    ),
    valid_states=[State.ADMIN_MENU]
)

CLOSE_PORT = Action(
    pattern=r'close port (?P<src_ip>[0-9.]+) (?P<src_port>\d+) '
    r'(?P<des_ip>[0-9.]+) (?P<des_port>\d+)',
    handler=lambda src_ip, src_port, des_ip, des_port, panel, **kwargs:
    panel.close_port(
        src_ip, src_port, des_ip, des_port, **kwargs
    ),
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

PASSWORD = Action(
    pattern=r'password (?P<password>.+)',
    handler=lambda password, panel, **kwargs: panel.password(
        password, **kwargs),
    valid_states=[State.INIT, State.ADMIN_ASK_PASSWORD]
)

FIREWALL_STATUS = Action(
    pattern=r'firewall status',
    handler=lambda panel, **kwargs: panel.firewall_status(**kwargs),
    valid_states=[State.ADMIN_MENU]
)


class Role:

    def __init__(self, name: str, actions: List[Action]):
        self.name = name
        self.actions = actions


ADMIN = Role(
    name=RoleNames.ADMIN,
    actions=[
        STATUS, BACK, SELECT, PASSWORD,
        SET_FIREWALL_KIND, OPEN_PORT, CLOSE_PORT,
        FIREWALL_STATUS
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


class GlobalVariables:
    users: List[User] = []
    active_users: List[User] = []
    next_id = 1
    lock = threading.Lock()
    admin_password = None


class SarPanel(BaseHandler):
    def __init__(self, config: dict = None):
        self.current_state = State.INIT
        self.ready = False
        self.killed_player_id = None
        self.finished = False
        self.config = config if config else {}
        self.user = None

    def _get_user(self, user_id: int) -> User:
        for user in GlobalVariables.users:
            if user.id == user_id:
                return user
        return None

    def _get_admin(self) -> User:
        for user in GlobalVariables.users:
            if user.role == ADMIN:
                return user
        return None

    def _get_player_by_role(self, role: Role):
        players = []
        for player in GlobalVariables.active_users:
            if player.role == role:
                players.append(player)
        return players

    def is_sar_ready(self):
        admin = self._get_admin()
        return bool(admin and admin.password)

    def _add_user(self, user):
        if self.is_sar_ready():
            GlobalVariables.users.append(user)
            GlobalVariables.active_users.append(user)
            user.role = ROLES_DICT[RoleNames.NORMAL]
            user.send_message("Connected to SAR Server!")
            self.current_state = State.MAIN_MENU

        elif not GlobalVariables.users:
            GlobalVariables.users.append(user)
            GlobalVariables.active_users.append(user)
            user.role = ROLES_DICT[RoleNames.ADMIN]
            user.send_message("Connected, You are admin!")
        else:
            user.send_message("SAR Server not ready! Please try again later.")
            user.socket.close()

    def handle(self, client: socket.socket, *args, **kwargs):
        GlobalVariables.lock.acquire()

        user = User(
            socket=client, id=GlobalVariables.next_id,
            panel=self, name=''
        )
        self.user = user

        GlobalVariables.next_id += 1

        self._add_user(user)

        GlobalVariables.lock.release()

        while True:
            try:
                user.send_message(State.state_string(self.current_state))
                print(self.user.socket.getpeername())
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
        GlobalVariables.users.remove(user)

    def back(self, **kwargs):
        user = self._get_user(kwargs.get('my_id'))
        if self.current_state == State.ADMIN_MENU:
            user.role = ROLES_DICT[RoleNames.NORMAL]

        self.current_state = State.prev(self.current_state)

    def status(self, **kwargs):
        user = self._get_user(kwargs.get('my_id'))
        user.send_message(State.state_string(self.current_state))

    def select(self, item_id, **kwargs):
        user = self._get_user(kwargs.get("my_id"))
        item_id = int(item_id)

        if self.current_state == State.MAIN_MENU:
            if item_id == 1:
                self.current_state = State.EXTERNAL_SERVERS
            elif item_id == 2:
                self.current_state = State.ADMIN_ASK_PASSWORD
            else:
                user.send_message("Wrong number!")
        elif self.current_state == State.EXTERNAL_SERVERS:
            if item_id == 1:
                transporter = Transporter(
                    src_socket=user.socket,
                    des_ip=SHALGHAM_IP,
                    des_port=SHALGHAM_PORT,
                    firewall=sar_firewall
                )
                transporter.start()
            elif item_id == 2:
                transporter = Transporter(
                    src_socket=user.socket,
                    des_ip=CHOGHONDAR_IP,
                    des_port=CHOGHONDAR_PORT,
                    firewall=sar_firewall
                )
                transporter.start()
            else:
                user.send_message("Wrong number!")

    def set_firewall_kind(self, firewall_kind, **kwargs):
        sar_firewall.set_kind(firewall_kind)

    def firewall_status(self, **kwargs):
        user = self._get_user(kwargs.get('my_id'))
        user.send_message(sar_firewall.status())

    def open_port(self, src_ip, src_port, des_ip, des_port, **kwargs):
        print("open", src_ip, src_port, des_ip, des_port)
        sar_firewall.open_port(
            src_ip=src_ip,
            src_port=src_port,
            des_ip=des_ip,
            des_port=des_port
        )

    def close_port(self, src_ip, src_port, des_ip, des_port, **kwargs):
        print("close", src_ip, src_port, des_ip, des_port)
        sar_firewall.close_port(
            src_ip=src_ip,
            src_port=src_port,
            des_ip=des_ip,
            des_port=des_port
        )

    def password(self, password, **kwargs):
        user = self._get_user(kwargs.get('my_id'))

        if self.current_state == State.INIT:
            user = self._get_user(kwargs.get('my_id'))
            GlobalVariables.admin_password = password
            user.password = password
            self.current_state = State.MAIN_MENU
        elif self.current_state == State.ADMIN_ASK_PASSWORD:
            if password == GlobalVariables.admin_password:
                user.role = ROLES_DICT[RoleNames.ADMIN]
                self.current_state = State.ADMIN_MENU
            else:
                user.send_message("Wrong password!")

    def inform_all(self, message, ignore_list=None):
        if not ignore_list:
            ignore_list = []
        for user in GlobalVariables.users:
            if user.id not in ignore_list:
                user.send_message(message)
