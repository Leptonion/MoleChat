from datetime import datetime
import requests
import json

from PyQt5.QtGui import QImage, QPixmap, QBrush, QPainter, QWindow
from PyQt5.QtCore import Qt, QRect


#  Singleton ABS
class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


#  Operator for cached Data!
class DataOperator(metaclass=Singleton):
    def __init__(self):
        self.cache = FileCache()

        self.user = None
        self.contacts = {}

        self.__route_dict = {"user": {"account": {"auth": self.__auth}},
                             "chat": {"item": {"create": self.__add_chat}},
                             "message": {"text": {"add": self.__add_message}}}

    def __auth(self, data: dict):
        self.user = User(us_id=data['id'], login=data['login'],
                         password=data['password'], nickname=data['nickname'],
                         avatar=data['avatar'], us_type=data['type'],
                         chats=data['chats'])
        for value in data['contacts'].values():
            value.update({'avatar': AvaPixmap(path=value['avatar'], place='box')})
        self.contacts.update(data['contacts'])

    def route_data(self, data: dict):
        return self.__route_dict[data['dest']][data['type']][data['action']](data['data'])

    def __add_message(self, data: dict):
        for x in self.user.chats:
            if data['chat_id'] == x.id:
                message = Message(ms_id=data['id'], owner_id=data['owner_id'],
                                  chat_id=data['chat_id'], post_date=data['post_date'],
                                  text=data['text'])
                x.posts.append(message)
                return message

    def __add_chat(self, data: dict):
        for value in data['contacts'].values():
            value.update({'avatar': AvaPixmap(path=value['avatar'], place='box')})
        self.contacts.update(data['contacts'])

        chat = Chat(ch_id=data['id'], title=data['title'],
                    participants=data['participants'], admin=data['admin'],
                    posts=[], avatar=data['avatar'])

        self.user.chats.insert(0, chat)
        return chat


#  User data pattern
class User:
    def __init__(self, us_id: int, login: str,
                 password: str, nickname: str, avatar: str,
                 us_type: int, chats: list):
        self.id = us_id
        self.login = login
        self.password = password
        self.nickname = nickname
        self.avatar = AvaPixmap(avatar, 'user')
        self.type = us_type

        self.chats = [Chat(ch_id=x['id'], title=x['title'],
                           participants=x['participants'],
                           admin=x['admin'], posts=x['posts'],
                           avatar=x['avatar']) for x in chats]
        self.__pre_sorting()

    def __pre_sorting(self):
        self.chats.sort(key=lambda x: x.last_post)


#  Chat data pattern
class Chat:
    def __init__(self, ch_id: int, title: str, participants: list,
                 admin: int, posts: list, avatar: str):
        self.id = ch_id
        self.title = title
        self.participants = participants
        self.admin = admin
        self.avatar = AvaPixmap(avatar, "chat")

        self.posts = [Message(ms_id=x['id'], owner_id=x['owner_id'],
                              chat_id=x['chat_id'], post_date=x['post_date'],
                              text=x['text']) for x in posts]
        self.__pre_sorting()

        self.last_post = self.posts[-1].post_date if self.posts else None

    def __pre_sorting(self):
        self.posts.sort(key=lambda x: x.post_date)


#  Message data pattern
class Message:
    def __init__(self, ms_id: int, owner_id: int, chat_id: int, post_date: str, text: str):
        self.id = ms_id
        self.owner = owner_id
        self.in_chat = chat_id
        self.post_date = datetime.strptime(post_date, '%m/%d/%Y, %H:%M:%S')
        self.text = text


# Pixmap converter pattern
class AvaPixmap:
    def __init__(self, path: str or None, place: str):
        self.image = QImage()
        self.sizes = {"box": 64,
                      "auth": None,
                      "user": 64,
                      "chat": 64}
        self.__func_dict = {"box": self.__circle,
                            "auth": self.__full,
                            "user": self.__circle,
                            "chat": self.__circle}

        if path:
            self.image.loadFromData(requests.get(f"http://127.0.0.1:8000/{path}").content)
        else:
            self.image = QImage("resources/mole_icon.png")

        self.pixmap = self.__func_dict[place](self.sizes[place])

    def __circle(self, size: int):
        self.image.convertToFormat(QImage.Format_ARGB32)

        imgsize = min(self.image.width(), self.image.height())
        rect = QRect(int((self.image.width() - imgsize) / 2),
                     int((self.image.height() - imgsize) / 2),
                     imgsize,
                     imgsize,)

        image = self.image.copy(rect)

        out_image = QImage(imgsize, imgsize, QImage.Format_ARGB32)
        out_image.fill(Qt.transparent)

        brush = QBrush(image)

        painter = QPainter(out_image)
        painter.setBrush(brush)

        painter.setPen(Qt.NoPen)

        painter.drawEllipse(0, 0, imgsize, imgsize)

        painter.end()

        pix_ratio = QWindow().devicePixelRatio()
        pixmap = QPixmap.fromImage(out_image)
        pixmap.setDevicePixelRatio(pix_ratio)
        size *= pix_ratio
        pixmap = pixmap.scaled(int(size), int(size), Qt.KeepAspectRatio, Qt.SmoothTransformation)

        return pixmap

    def __full(self, size):
        return QPixmap(self.image)


# Static data cache class
class FileCache:
    def __init__(self):
        self.address = None
        self.main_port = None
        self.stor_port = None

        self.__fill_main_data()

    def __fill_main_data(self):
        with open('bin/cdf.json', 'r') as file:
            json_obj = json.load(file)

            self.address = json_obj['address']
            self.main_port = json_obj['main_port']
            self.stor_port = json_obj['stor_port']
