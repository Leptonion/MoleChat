**MoleChat**

Simple messenger application. 
The application is intended for private use and is under development. The main goal of the project is to familiarize yourself with the Twisted and PyQt5 frameworks.

    Don`t use application in the public domain!
    The application is not intended for a high-load environment (not designed for a huge number of users)!

**First start - Server:**

Server used PostGreSQL Database!

Environment variables:
 - ENV ADDRESS (main server IP address)
 - ENV MAIN_PORT (main transport port)
 - ENV STOR_PORT (file storage port)
 - ENV DB_ADDRESS (database IP address:port)
 - ENV DB_TABLE_NAME (database tablename)
 - ENV DB_LOGIN (database login)
 - ENV DB_PASS (database password)

Starting dot - _core.py_

**First start - Client:**

Before the first launch, you must fill in the fields in the file _"Client/bin/cdf.json"_:
 - address (Server IP address)
 - main_port (Server port)
 - stor_port (file storage port)

Starting dot - _application.py_

    Client don`t work without Server connection!

**About**

At the moment, the project has implemented minimal functionality:
 - User authentication
 - Creating new chats.
 - Sending messages.

**Note**

In the future, the project will be supplemented and expanded, along with this a more detailed and correct README will be attached.
At the moment the project is in a very raw state.