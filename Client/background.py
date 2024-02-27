from twisted.internet.protocol import Protocol
from twisted.internet.protocol import ClientFactory as ClFactory

import json

from cached import DataOperator


operator = DataOperator()


# App to Server connection constructor
class Client(Protocol):
    def __init__(self, interface):
        self.auth_state = None
        self.push = InterfaceRelationship(interface)

    def dataReceived(self, data: bytes):
        data = data.decode("utf-8")
        data = json.loads(data)
        self.push.translate_to_interface(data)

    def send_data(self, data: dict):
        self.transport.write(json.dumps(data).encode("utf-8"))


class ClientFactory(ClFactory):
    def __init__(self, proto):
        self.proto = proto

    def buildProtocol(self, addr):
        return self.proto


# Relationship class - Interface <-> Server
class InterfaceRelationship:
    def __init__(self, interface):
        self.interface = interface
        self.auth_state = False

        self.__route_dict = {"user": {"account": {"auth": self.__authentication},
                                      "contacts": {"search": self.__users_list}},
                             "chat": {"item": {"create": self.__new_chat}},
                             "message": {"text": {"add": self.__new_message}}}

    def translate_to_interface(self, data: dict):
        return self.__route_dict[data['dest']][data['type']][data['action']](data)

    def __authentication(self, data):
        if not self.auth_state:
            if data['response'] == "Success":
                operator.route_data(data)
                self.auth_state = True
                self.interface = self.interface.transfer_to_main()

            elif data['response'] == "Declined":
                self.interface.wrong_auth_data(data['message'])

            else:
                self.interface.close()

    def __new_message(self, data):
        if data['response'] == "Success":
            dt_obj = operator.route_data(data)
            self.interface.show_new_message(dt_obj)

        elif data['response'] == "Failed":
            ...

    def __users_list(self, data):
        if data['response'] == "Success":
            self.interface.chat_editor.show_users_list(data['data'])

        elif data['response'] == "Failed":
            ...

    def __new_chat(self, data):
        if data['response'] == "Success":
            ch_obj = operator.route_data(data)
            self.interface.show_new_chat(ch_obj)

        elif data['response'] == "Failed":
            ...
