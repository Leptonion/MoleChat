import sys

from PyQt5.QtWidgets import QApplication
from interface import LoginPage


if __name__ == "__main__":
    app = QApplication(sys.argv)

    import qt5reactor

    qt5reactor.install()

    from twisted.internet import reactor

    login_page = LoginPage(reactor)
    login_page.show()

    reactor.run()
    sys.exit(app.exec_())
