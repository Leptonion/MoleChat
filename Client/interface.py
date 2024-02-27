from PyQt5 import uic, QtCore, QtWidgets, QtGui, sip
from PyQt5.QtWidgets import QMainWindow, QLabel, QMessageBox

from twisted.internet.endpoints import TCP4ClientEndpoint

from cached import DataOperator, AvaPixmap
from background import Client, ClientFactory

operator = DataOperator()


# Main window
class App(QMainWindow):
    def __init__(self, reactor, protocol, p_factory):
        super().__init__()
        uic.loadUi('MoleChat.ui', self)

        # Set window/button icons
        self.setWindowIcon(QtGui.QIcon("resources/mole_icon.png"))

        self.send_button.setIcon(QtGui.QIcon("resources/send_button.png"))
        self.send_button.setIconSize(QtCore.QSize(26, 26))

        self.gif_button.setIcon(QtGui.QIcon("resources/giphy.svg"))
        self.gif_button.setIconSize(QtCore.QSize(22, 18))

        self.control_button_1.setIcon(QtGui.QIcon("resources/create_group_button.png"))
        self.control_button_1.setIconSize(QtCore.QSize(22, 18))

        # init transport objects
        self.reactor = reactor
        self.protocol = protocol
        self.p_factory = p_factory

        self.chat_editor = None

        # Set links for dynamic interface components
        self.current_box = None
        self.current_layout = None
        self.current_chat_layout = self.verticalLayout_4
        self.current_scrollArea = self.scrollAreaWidgetContents_2
        self.last_message_owner = None
        self.current_row = None

        # Set static pixmaps
        self.label.setPixmap(operator.user.avatar.pixmap)
        self.chat_ava.setPixmap(operator.user.avatar.pixmap)

        # Set Nickname
        self.label_2.setText(f'<html><head/><body><p align="center">'
                             f'<span style=" font-size:10pt;">{operator.user.nickname}</span></p></body></html>')

        # Disable interaction components on first start (if chat isn`t selected)
        self.send_button.setEnabled(False)
        self.message_input.setEnabled(False)
        self.gif_button.setEnabled(False)

        # Fill chat list
        for i in operator.user.chats:
            item = QtWidgets.QListWidgetItem()
            item.setText(i.title)
            self.chat_list.addItem(item)

        # Activate interaction components (signals)
        self.__action_functions()

        # Set event filter on message input form (Enter press signal)
        self.message_input.installEventFilter(self)

    # Event filter for message input form (Enter press signal)
    def eventFilter(self, obj, event):
        if obj is self.message_input and event.type() == QtCore.QEvent.KeyPress:
            if event.key() in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter)\
                    and event.modifiers() != QtCore.Qt.KeyboardModifier.ShiftModifier:
                self.__send_message(self.message_input.toPlainText())
                return True

        return super().eventFilter(obj, event)

    # Creating interaction components (signals)
    def __action_functions(self):
        self.chat_list.currentRowChanged.connect(lambda: self.__change_chat())
        self.send_button.clicked.connect(lambda: self.__send_message(self.message_input.toPlainText()))
        self.control_button_1.clicked.connect(lambda: self.__new_chat())

    # Change chat function
    def __change_chat(self):
        self.current_row = self.chat_list.currentRow()
        self.__delete_old_chat()
        self.last_message_owner = None
        self.__chat_constructor(operator.user.chats[self.current_row])

        if not self.send_button.isEnabled():
            self.send_button.setEnabled(True)
        if not self.message_input.isEnabled():
            self.message_input.setEnabled(True)
        # if not self.gif_button.isEnabled():
        #     self.gif_button.setEnabled(True)

    # Clear messages field before changes
    def __delete_old_chat(self):
        self.current_chat_layout.removeWidget(self.current_scrollArea)
        sip.delete(self.current_scrollArea)
        self.current_scrollArea = None

    # Filling messages field
    def __chat_constructor(self, data):
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, -65, 536, 666))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.current_scrollArea = self.scrollAreaWidgetContents

        self.verticalLayout = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout.setObjectName(f"verticalLayout1_{data.id}")
        self.current_chat_layout = self.verticalLayout

        self.empty_message_frame = QtWidgets.QFrame(self.scrollAreaWidgetContents)
        self.empty_message_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.empty_message_frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.empty_message_frame.setObjectName(f"empty_message_frame_{data.id}")

        self.verticalLayout_1 = QtWidgets.QVBoxLayout(self.empty_message_frame)
        self.verticalLayout_1.setObjectName(f"verticalLayout2_{data.id}")

        spacerItem = QtWidgets.QSpacerItem(20, 326, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_1.addItem(spacerItem)

        self.verticalLayout.addWidget(self.empty_message_frame)

        self.chat_name.setText(f"<html><head/><body><p><span style=\" font-size:12pt;\">{data.title}</span></p></body></html>")
        self.chat_ava.setPixmap(data.avatar.pixmap)

        for row in data.posts:

            if row.owner == operator.user.id:
                if self.last_message_owner == row.owner:
                    self.new_out_label(row)
                else:
                    self.new_out_box(row)

            else:
                if self.last_message_owner == row.owner:
                    self.new_in_label(row)
                else:
                    self.new_in_box(row)

        self.chat_area.setWidget(self.scrollAreaWidgetContents)

    # New message box from self
    def new_out_box(self, message):
        if message:
            self.new_owner_message_frame = QtWidgets.QFrame()
            self.new_owner_message_frame.setMinimumSize(QtCore.QSize(0, 100))
            self.new_owner_message_frame.setLayoutDirection(QtCore.Qt.RightToLeft)
            self.new_owner_message_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
            self.new_owner_message_frame.setFrameShadow(QtWidgets.QFrame.Raised)
            self.new_horizontalLayout_6 = QtWidgets.QHBoxLayout(self.new_owner_message_frame)

            self.new_owner_message_box = QtWidgets.QWidget(self.new_owner_message_frame)
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(self.new_owner_message_box.sizePolicy().hasHeightForWidth())
            self.new_owner_message_box.setSizePolicy(sizePolicy)
            self.new_owner_message_box.setLayoutDirection(QtCore.Qt.RightToLeft)
            self.new_owner_message_box.setAutoFillBackground(False)
            self.new_owner_message_box.setStyleSheet("")
            self.new_owner_message_box.setObjectName(f"self.new_owner_message_box_{message.id}")

            self.new_formLayout_2 = QtWidgets.QFormLayout(self.new_owner_message_box)
            self.new_formLayout_2.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
            self.new_formLayout_2.setObjectName(f"new_formLayout_2_{message.id}")

            self.new_owner_message = QtWidgets.QLabel(self.new_owner_message_box)
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Maximum)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(self.new_owner_message.sizePolicy().hasHeightForWidth())
            self.new_owner_message.setSizePolicy(sizePolicy)
            self.new_owner_message.setMinimumSize(QtCore.QSize(0, 0))
            self.new_owner_message.setMaximumSize(QtCore.QSize(450, 16777215))
            self.new_owner_message.setStyleSheet("QLabel {\n"
                                               "    background-color: rgb(6, 89, 190);\n"
                                               "    border-top-left-radius: 7px;\n"
                                               "    border-bottom-right-radius: 7px;\n"
                                               "    border-bottom-left-radius: 7px;\n"
                                               "    padding: 3px;\n"
                                               "}")
            self.new_owner_message.setScaledContents(True)
            self.new_owner_message.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
            self.new_owner_message.setWordWrap(True)

            self.new_formLayout_2.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.new_owner_message)

            self.new_horizontalLayout_6.addWidget(self.new_owner_message_box)
            self.new_empty_widget = QtWidgets.QWidget(self.new_owner_message_frame)
            self.new_horizontalLayout_6.addWidget(self.new_empty_widget)
            self.current_chat_layout.addWidget(self.new_owner_message_frame)

            self.new_owner_message.setText(message.text)

            self.current_box = self.new_owner_message
            self.current_layout = self.new_formLayout_2
            self.last_message_owner = message.owner

    # New message from self
    def new_out_label(self, message):
        if message:
            self.new_label = QtWidgets.QLabel()
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Maximum)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(self.new_label.sizePolicy().hasHeightForWidth())
            self.new_label.setSizePolicy(sizePolicy)
            self.new_label.setMinimumSize(QtCore.QSize(0, 0))
            self.new_label.setMaximumSize(QtCore.QSize(450, 16777215))
            self.new_label.setStyleSheet("QLabel {\n"
                                       "    background-color: rgb(6, 89, 190);\n"
                                       "    border-top-left-radius: 7px;\n"
                                       "    border-bottom-right-radius: 7px;\n"
                                       "    border-bottom-left-radius: 7px;\n"
                                       "    padding: 3px;\n"
                                       "}")
            self.new_label.setScaledContents(True)
            self.new_label.setWordWrap(True)
            self.new_label.setAlignment(QtCore.Qt.AlignRight)
            self.new_label.setText(message.text)

            self.current_layout.addRow(self.new_label)

    # New message box from participant
    def new_in_box(self, message):
        if message:
            self.new_user_message_frame = QtWidgets.QFrame()
            self.new_user_message_frame.setMinimumSize(QtCore.QSize(0, 100))
            self.new_user_message_frame.setLayoutDirection(QtCore.Qt.LeftToRight)
            self.new_user_message_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
            self.new_user_message_frame.setFrameShadow(QtWidgets.QFrame.Raised)
            self.new_horizontalLayout_8 = QtWidgets.QHBoxLayout(self.new_user_message_frame)
            self.new_horizontalLayout_8.setContentsMargins(-1, 9, -1, -1)
            self.new_user_message_ava = QtWidgets.QFrame(self.new_user_message_frame)
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Minimum)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(self.new_user_message_ava.sizePolicy().hasHeightForWidth())
            self.new_user_message_ava.setSizePolicy(sizePolicy)
            self.new_user_message_ava.setMinimumSize(QtCore.QSize(70, 70))
            self.new_user_message_ava.setMaximumSize(QtCore.QSize(70, 16777215))
            self.new_user_message_ava.setBaseSize(QtCore.QSize(0, 0))
            self.new_user_message_ava.setStyleSheet("background-color: rgb(6, 89, 190);")
            self.new_user_message_ava.setFrameShape(QtWidgets.QFrame.StyledPanel)
            self.new_user_message_ava.setFrameShadow(QtWidgets.QFrame.Raised)
            self.new_user_message_ava.setObjectName(f"new_user_message_ava_{message.id}")
            self.new_verticalLayout_5 = QtWidgets.QVBoxLayout(self.new_user_message_ava)
            self.new_verticalLayout_5.setContentsMargins(-1, 9, -1, -1)
            self.new_verticalLayout_5.setObjectName(f"new_verticalLayout_5_{message.id}")
            self.new_user_ava = QtWidgets.QLabel(self.new_user_message_ava)
            self.new_user_ava.setMinimumSize(QtCore.QSize(50, 50))
            self.new_user_ava.setMaximumSize(QtCore.QSize(50, 50))
            self.new_user_ava.setStyleSheet("")
            self.new_user_ava.setText("")
            self.new_user_ava.setPixmap(operator.contacts[str(message.owner)]['avatar'].pixmap)
            self.new_user_ava.setScaledContents(True)
            self.new_user_ava.setOpenExternalLinks(False)
            self.new_user_ava.setObjectName(f"new_user_ava_{message.id}")
            self.new_verticalLayout_5.addWidget(self.new_user_ava)
            self.new_user_name = QtWidgets.QLabel(self.new_user_message_ava)
            self.new_user_name.setObjectName(f"new_user_name_{message.id}")
            self.new_user_name.setText(str(operator.contacts[str(message.owner)]['nickname']))
            self.new_verticalLayout_5.addWidget(self.new_user_name)
            self.new_horizontalLayout_8.addWidget(self.new_user_message_ava)
            self.new_user_message_box = QtWidgets.QWidget(self.new_user_message_frame)
            self.new_user_message_box.setLayoutDirection(QtCore.Qt.LeftToRight)
            self.new_user_message_box.setStyleSheet("")
            self.new_user_message_box.setObjectName(f"new_user_message_box_{message.id}")
            self.new_formLayout = QtWidgets.QFormLayout(self.new_user_message_box)
            self.new_formLayout.setObjectName(f"new_formLayout_{message.id}")
            self.new_user_message = QtWidgets.QLabel(self.new_user_message_box)
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Maximum)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(self.new_user_message.sizePolicy().hasHeightForWidth())
            self.new_user_message.setSizePolicy(sizePolicy)
            self.new_user_message.setMaximumSize(QtCore.QSize(450, 16777215))
            self.new_user_message.setStyleSheet("QLabel {\n"
                                                "    background-color: rgb(6, 89, 190);\n"
                                                "    border-top-right-radius: 7px;\n"
                                                "    border-bottom-right-radius: 7px;\n"
                                                "    border-bottom-left-radius: 7px;\n"
                                                "    padding: 3px;\n"
                                                "}")
            self.new_user_message.setWordWrap(True)
            self.new_user_message.setObjectName(f"new_user_message_{message.id}")
            self.new_formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.new_user_message)
            self.new_horizontalLayout_8.addWidget(self.new_user_message_box)
            self.current_chat_layout.addWidget(self.new_user_message_frame)

            self.new_user_message.setText(message.text)

            self.current_box = self.new_user_message
            self.current_layout = self.new_formLayout
            self.last_message_owner = message.owner

    # New message from participant (in same participant box)
    def new_in_label(self, message):
        if message:
            self.new_label = QtWidgets.QLabel(self.current_box)
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Maximum)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(self.new_label.sizePolicy().hasHeightForWidth())
            self.new_label.setSizePolicy(sizePolicy)
            self.new_label.setMinimumSize(QtCore.QSize(0, 0))
            self.new_label.setMaximumSize(QtCore.QSize(450, 16777215))
            self.new_label.setStyleSheet("QLabel {\n"
                                         "    background-color: rgb(6, 89, 190);\n"
                                         "    border-top-right-radius: 7px;\n"
                                         "    border-bottom-right-radius: 7px;\n"
                                         "    border-bottom-left-radius: 7px;\n"
                                         "    padding: 3px;\n"
                                         "}")
            self.new_label.setScaledContents(True)
            self.new_label.setWordWrap(True)
            self.new_label.setAlignment(QtCore.Qt.AlignLeft)
            self.new_label.setText(message.text)

            self.current_layout.addRow(self.new_label)

    # Send new message - Interface -> Server
    def __send_message(self, text: str):
        if text:
            message = {"dest": "message", "type": "text",
                       "action": "add", "data": {"owner_id": operator.user.id,
                                                 "chat_id": operator.user.chats[self.current_row].id,
                                                 "text": text}}
            self.protocol.send_data(message)
            self.message_input.setText("")

    # Showing new message (selected chat) - Server -> Interface
    def show_new_message(self, data):
        if data.in_chat == operator.user.chats[self.current_row].id:
            if data.owner == operator.user.id:
                if self.last_message_owner == data.owner:
                    self.new_out_label(data)
                else:
                    self.new_out_box(data)

            else:
                if self.last_message_owner == data.owner:
                    self.new_in_label(data)
                else:
                    self.new_in_box(data)

    # Open chat creation window
    def __new_chat(self):
        if self.chat_editor:
            self.chat_editor.close()

        self.chat_editor = ModalChatEditor(self.protocol)
        self.chat_editor.show()

    # Showing new chat - Server -> Interface
    def show_new_chat(self, ch_obj):
        item = QtWidgets.QListWidgetItem()
        item.setText(ch_obj.title)
        self.chat_list.insertItem(0, item)
        self.current_row = self.chat_list.currentRow()


# Login window
class LoginPage(QMainWindow):
    def __init__(self, reactor):
        super().__init__()
        uic.loadUi('LoginWindow.ui', self)

        # Set window icons
        self.setWindowIcon(QtGui.QIcon("resources/mole_icon.png"))

        # Set logo
        self.login_logo_pic.setPixmap(AvaPixmap(path=None, place='auth').pixmap)

        # Activate interaction components (signals)
        self.functions()

        # Create server connection
        self.reactor = reactor
        self.protocol = Client(self)
        self.pf = ClientFactory(self.protocol)

        endpoint = TCP4ClientEndpoint(self.reactor,
                                      operator.cache.address,
                                      operator.cache.main_port)
        endpoint.connect(self.pf)

    # Creating interaction components (signals)
    def functions(self):
        self.authButton.clicked.connect(lambda: self.__authenticate())

    # Authentication function
    def __authenticate(self):
        login = self.login_text_input.text()
        password = self.password_text_input.text()
        self.protocol.send_data({"dest": "user",
                                 "type": "account",
                                 "action": "auth",
                                 "data": {"login": f"{login}",
                                          "password": f"{password}"}})

    # Show wrong auth data label
    def wrong_auth_data(self, message: str):
        login_error_label = QLabel(self)
        login_error_label.setGeometry(QtCore.QRect(110, 330, 111, 16))
        login_error_label.setObjectName("login_error_label")
        login_error_label.setText(f"<html><head/><body><p align=\"center\">"
                                  f"<span style=\" color:#ff0000;\">{message}</span></p></body></html>")
        login_error_label.show()

    # Show main app window
    def transfer_to_main(self):
        main_app = App(self.reactor, self.protocol, self.pf)
        main_app.show()
        self.close()
        return main_app


# Chat added window
class ModalChatEditor(QtWidgets.QWidget):
    def __init__(self, protocol):
        super().__init__()
        uic.loadUi('ChatEditor_add.ui', self)

        # Set window icon
        self.setWindowIcon(QtGui.QIcon("resources/create_group_button.png"))

        # Connection object
        self.protocol = protocol

        # Interactive lists
        self.user_list = [operator.user.id]
        self.button_list = []

        # Activate interaction components (signals)
        self.__actions()

    # Creating interaction components (signals)
    def __actions(self):
        self.chat_editor_searh_lineEdit.returnPressed.connect(lambda: self.__send_users_list())
        self.create_chat.clicked.connect(lambda: self.__send_create_chat())

    # Request searched users list - Interface -> Server
    def __send_users_list(self):
        search_text = self.chat_editor_searh_lineEdit.text()

        self.protocol.send_data({"dest": "user",
                                 "type": "contacts",
                                 "action": "search",
                                 "data": {"text": search_text}})

    # Clear searched users lis (in Interface)
    def __clear_list(self):
        self.chat_editor_formLayout.removeWidget(self.scrollAreaWidgetContents)
        sip.delete(self.scrollAreaWidgetContents)
        self.scrollAreaWidgetContents = None

    # Show searched users list - Server -> Interface
    def show_users_list(self, users: list):
        self.__clear_list()

        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setStyleSheet("QCheckBox {\n"
                                                    "    background-color: rgb(142, 167, 255);\n"
                                                    "}")
        self.chat_editor_formLayout = QtWidgets.QFormLayout(self.scrollAreaWidgetContents)

        for i, x in enumerate(users):
            self.pushButton = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
            self.pushButton.setMaximumSize(QtCore.QSize(25, 16777215))
            self.pushButton.setStyleSheet("QPushButton {\n"
                                          "    background-color: rgb(39, 170, 37);\n"
                                          "    padding: 9px 15px 9px;\n"
                                          "}")
            self.pushButton.setObjectName(f"pushButton_{i + 1}")
            self.pushButton.setText("+")
            self.chat_editor_formLayout.setWidget(i + 1, QtWidgets.QFormLayout.FieldRole, self.pushButton)
            self.label = QtWidgets.QLabel(self.scrollAreaWidgetContents)
            self.label.setStyleSheet("QLabel {\n"
                                     "    background-color: rgb(142, 167, 255);\n"
                                     "    padding: 9px 15px 9px;\n"
                                     "}")
            self.label.setObjectName(f"label_{i + 1}")
            self.label.setText(f"{x['nickname']} (@{x['login']})")
            self.chat_editor_formLayout.setWidget(i + 1, QtWidgets.QFormLayout.LabelRole, self.label)

            self.pushButton.clicked.connect(lambda checked, i=x['id'], b=self.pushButton: self.__add_button_pressed(b, i))

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

    # Item checked button in searched user list
    def __add_button_pressed(self, button, us_id):
        if button.text() == "+":
            self.user_list.append(us_id)
            button.setText("-")
            button.setStyleSheet("QPushButton {\n"
                                                   "    background-color: rgb(212, 0, 0);\n"
                                                   "    padding: 9px 15px 9px;\n"
                                                   "}")
            button.update()

        elif button.text() == "-":
            self.user_list.remove(us_id)
            button.setText("+")
            button.setStyleSheet("QPushButton {\n"
                                 "    background-color: rgb(39, 170, 37);\n"
                                 "    padding: 9px 15px 9px;\n"
                                 "}")
            button.update()

    # Create chat request - Interface -> Server
    def __send_create_chat(self):
        title = self.chat_editor_line_edit.text()
        if not title or title.isspace():
            #  Show messageBox with error - Unfilled title!
            msg = QMessageBox()
            msg.setWindowTitle("Declined")
            msg.setText("Unfilled title - please enter the title!")
            msg.setIcon(QMessageBox.Warning)

            msg.exec_()

        elif len(self.user_list) < 2:
            #  Show messageBox with error - Need to add one or more participants!
            msg = QMessageBox()
            msg.setWindowTitle("Declined")
            msg.setText("No one participants is selected - please select one or more participants!")
            msg.setIcon(QMessageBox.Warning)

            msg.exec_()

        else:
            self.protocol.send_data({"dest": "chat",
                                     "type": "item",
                                     "action": "create",
                                     "data": {"title": title,
                                              "participants": self.user_list,
                                              "admin": operator.user.id}})
        self.close()
