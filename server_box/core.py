from twisted.internet import reactor
from twisted.internet.protocol import Protocol
from twisted.internet.protocol import ServerFactory as ServFactory
from twisted.internet.endpoints import TCP4ServerEndpoint

from http.server import HTTPServer as BaseHTTPServer, SimpleHTTPRequestHandler

from data_router import DataOpera
from db_core import DataBaseConnector

import json
import os


# Connection attributes (get from environment variables)
class ConnAttr:
    def __init__(self):
        self.address = os.environ.get('ADDRESS')
        self.main_port = int(os.environ.get('MAIN_PORT'))
        self.stor_port = int(os.environ.get('STOR_PORT'))

        self.db = DBAttr()


class DBAttr:
    def __init__(self):
        self.address = os.environ.get('DB_ADDRESS')
        self.table_name = os.environ.get('DB_TABLE_NAME')
        self.login = os.environ.get('DB_LOGIN')
        self.password = os.environ.get('DB_PASS')


#  Server protocol!
class Server(Protocol):
    def __init__(self, connections):
        self.connections = connections
        self.__operator = DataOpera()

    def connectionMade(self):
        print(f"New connection - {self}")

    def connectionLost(self, reason):
        for connection in self.connections:
            if self == connection[1]:
                self.connections.remove(connection)

    def dataReceived(self, data: bytes):
        data = data.decode("utf-8")
        data = json.loads(data)
        participants, response = self.__operator.route_data(data['dest'],
                                                            data['type'],
                                                            data['action'],
                                                            data['data'])

        #  Self response
        if not participants and response['response'] == 'Success':
            if response['action'] == "auth":
                self.connections.append([response['data']['id'], self])
            self.transport.write(json.dumps(response).encode("utf-8"))

        #  Party response
        elif participants and response['response'] == 'Success':
            for connection in self.connections:
                if connection[0] in participants:
                    connection[1].transport.write(json.dumps(response).encode("utf-8"))

        #  Error response
        else:
            self.transport.write(json.dumps(response).encode("utf-8"))


#  Server Factory
class ServerFactory(ServFactory):
    def __init__(self):
        self.connections = []

    def buildProtocol(self, addr):
        return Server(self.connections)


# File Server (based on simple HTTP)
class FServerHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path: str) -> str:
        path = SimpleHTTPRequestHandler.translate_path(self, path)
        relpath = os.path.relpath(path, os.getcwd())
        fullpath = os.path.join(self.server.base_path, relpath)
        return fullpath


class FileServer(BaseHTTPServer):
    def __init__(self, base_path, server_address, handler_class=FServerHandler):
        self.base_path = base_path
        BaseHTTPServer.__init__(self, server_address, handler_class)


def run_fileserver():
    web_dir = os.path.join(os.path.dirname(__file__), 'resources')
    httpd = FileServer(web_dir, ("", conn_attr.stor_port))
    print("start file server", f"Port - {conn_attr.stor_port}")
    httpd.serve_forever()


if __name__ == "__main__":
    conn_attr = ConnAttr()
    db = DataBaseConnector()
    db.set_parameters(conn_attr.db.address, conn_attr.db.table_name, conn_attr.db.login, conn_attr.db.password)
    db.create_db()
    endpoint = TCP4ServerEndpoint(reactor, conn_attr.main_port)
    endpoint.listen(ServerFactory())
    reactor.callInThread(run_fileserver)
    reactor.run()
