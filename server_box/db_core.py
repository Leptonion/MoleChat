from sqlalchemy import Column, Text, BigInteger, Integer, DateTime, ARRAY, ForeignKey, create_engine
from sqlalchemy.orm import relationship, DeclarativeBase, backref, scoped_session, sessionmaker


#  Singleton ABS
class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


#  Database patterns
class Base(DeclarativeBase):
    ...


class Users(Base):
    __tablename__ = "users"

    id = Column(BigInteger, nullable=False, primary_key=True, autoincrement=True)
    login = Column(Text, nullable=False)
    password = Column(Text, nullable=False)
    nickname = Column(Text, nullable=False)
    us_type = Column(Integer, nullable=False)
    ava = Column(Text)


class Chats(Base):
    __tablename__ = "chats"

    id = Column(BigInteger, nullable=False, primary_key=True, autoincrement=True)
    title = Column(Text, nullable=False)
    participants = Column(ARRAY(Integer), nullable=False)
    contacts = Column(ARRAY(Integer), nullable=False)
    admin = Column(Integer, nullable=False)
    ava = Column(Text)


class Messages(Base):
    __tablename__ = "messages"

    id = Column(BigInteger, nullable=False, primary_key=True, autoincrement=True)
    owner_id = Column(ForeignKey("users.id"), nullable=False)
    chat_id = Column(ForeignKey("chats.id"), nullable=False)
    post_date = Column(DateTime, nullable=False)
    text = Column(Text, nullable=False)

    parent_chat = relationship("Chats", backref=backref("posts", lazy="dynamic"))


# DB Connector
class DataBaseConnector(metaclass=Singleton):
    def __init__(self):
        self.__server = None
        self.__name = None
        self.__login = None
        self.__password = None
        self.__engine = None
        self.session = None
        self.state = False

    def set_parameters(self, server, name, login, password):
        self.__server = server
        self.__name = name
        self.__login = login
        self.__password = password
        self.session = self.__session_engine()

    def create_db(self):
        Base.metadata.create_all(bind=self.__engine)

    def __get_parameters(self):
        return f"postgresql+psycopg2://{self.__login}:{self.__password}@{self.__server}/{self.__name}"

    def __session_engine(self):
        engine = create_engine(self.__get_parameters())
        self.__engine = engine
        session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        return scoped_session(session_factory)

    def __enter__(self):
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
