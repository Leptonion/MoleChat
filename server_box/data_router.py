from db_core import Chats, Users, Messages, DataBaseConnector
from sqlalchemy import or_
from datetime import datetime


#  Main DATA route class
class DataOpera:
    def __init__(self):
        self.message = Message()
        self.chat = Chat()
        self.user = User()

        self.__route_dict = {"user": {"account": {"auth": self.user.authenticate},
                                      "contacts": {"search": self.user.search_users}},
                             "chat": {"item": {"create": self.chat.new}},
                             "message": {"text": {"add": self.message.new}}}

    def route_data(self, r_dest: str, r_type: str, r_action: str, data: dict):
        return self.__route_dict[r_dest][r_type][r_action](data)


#  Message Operator class
class Message:
    def __init__(self):
        self.cursor = DataBaseConnector()

    def new(self, data: dict):
        try:
            with self.cursor as session:
                row = Messages(owner_id=data['owner_id'],
                               chat_id=data['chat_id'],
                               post_date=datetime.now(),
                               text=data['text'])
                session.add(row)
                session.commit()

                chat = session.query(Chats).filter_by(id=data['chat_id']).first()
                participants = chat.participants

                response = {"dest": "message",
                            "type": "text",
                            "action": "add",
                            "response": "Success",
                            "message": "Message is added to chat!",
                            "data": {"id": row.id,
                                     "owner_id": row.owner_id,
                                     "chat_id": row.chat_id,
                                     "post_date": row.post_date.strftime("%m/%d/%Y, %H:%M:%S"),
                                     "text": row.text}}

                return participants, response
        except:
            return None, {"dest": "message",
                          "type": "text",
                          "action": "add",
                          "response": "Failed",
                          "message": "Message isn`t added to chat!",
                          "data": None}


#  Chat Operator class
class Chat:
    def __init__(self):
        self.cursor = DataBaseConnector()

    def new(self, data: dict):
        try:
            with self.cursor as session:
                row = Chats(title=data['title'], participants=data['participants'],
                            contacts=data['participants'], admin=data['admin'])

                session.add(row)
                session.commit()

                contacts = session.query(Users).filter(Users.id.in_(row.contacts)).all()

                response = {"dest": "chat",
                            "type": "item",
                            "action": "create",
                            "response": "Success",
                            "message": "New chat is created!",
                            "data": {"id": row.id,
                                     "title": row.title,
                                     "participants": row.participants,
                                     "avatar": row.ava,
                                     "contacts": {x.id: {"login": x.login,
                                                         "nickname": x.nickname,
                                                         "avatar": x.ava} for x in contacts},
                                     "admin": row.admin}}

                return row.participants, response
        except:
            return None, {"dest": "chat",
                          "type": "item",
                          "action": "create",
                          "response": "Failed",
                          "message": "Chat isn`t created!",
                          "data": None}


#  User Operator class
class User:
    def __init__(self):
        self.cursor = DataBaseConnector()

    @staticmethod
    def __posts_converter(post_obj):
        result = post_obj.order_by(Messages.id.desc()).limit(25)
        return [{"id": x.id,
                 "owner_id": x.owner_id,
                 "chat_id": x.chat_id,
                 "post_date": x.post_date.strftime("%m/%d/%Y, %H:%M:%S"),
                 "text": x.text} for x in result]

    def authenticate(self, data: dict):
        try:
            with self.cursor as session:
                user = session.query(Users).filter_by(login=data['login'], password=data['password']).first()

                if not user:
                    return None, {"dest": "user",
                                  "type": "account",
                                  "action": "auth",
                                  "response": "Declined",
                                  "message": "Wrong Login/Password!",
                                  "data": None}

                chats = session.query(Chats).filter(Chats.contacts.any(user.id)).all()

                con_ids = set()
                for x in chats:
                    con_ids.update(x.contacts)

                contacts = session.query(Users).filter(Users.id.in_(list(con_ids))).all()

                full_data = {"id": user.id,
                             "login": user.login,
                             "password": None,
                             "nickname": user.nickname,
                             "type": user.us_type,
                             "contacts": {x.id: {"login": x.login,
                                                 "nickname": x.nickname,
                                                 "avatar": x.ava} for x in contacts},
                             "avatar": user.ava,
                             "chats": [{"id": x.id,
                                        "title": x.title,
                                        "participants": x.participants,
                                        "admin": x.admin,
                                        "avatar": x.ava,
                                        "posts": self.__posts_converter(x.posts)} for x in chats]}

                return None, {"dest": "user",
                              "type": "account",
                              "action": "auth",
                              "response": "Success",
                              "message": f"User {user.nickname} is authenticated!",
                              "data": full_data}

        except:
            return None, {"dest": "user",
                          "type": "account",
                          "action": "auth",
                          "response": "Failed",
                          "message": f"Something went wrong - Server error!",
                          "data": None}

    def search_users(self, data: dict):
        try:
            with self.cursor as session:
                users = session.query(Users).filter(or_(Users.login.like(f"%{data['text']}%"),
                                                        Users.nickname.like(f"%{data['text']}%"))).all()
                return None, {"dest": "user",
                              "type": "contacts",
                              "action": "search",
                              "response": "Success",
                              "message": "List of searched users",
                              "data": [{"id": x.id,
                                        "login": x.login,
                                        "nickname": x.nickname} for x in users]}
        except:
            return None, {"dest": "user",
                          "type": "contacts",
                          "action": "search",
                          "response": "Failed",
                          "message": f"Something went wrong - Server error!",
                          "data": None}
