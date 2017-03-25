from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///msgs.db.sqlite', echo=False)
Session = sessionmaker(bind=engine)
Base = declarative_base()


@contextmanager
def session_context():
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


class Msg(Base):
    __tablename__ = 'msgs'

    id = Column(Integer, primary_key=True)
    to_user = Column(String)
    subject = Column(String)
    content = Column(String)


def msg_to_dict(msg):
    return {
        'id': msg.id,
        'subject': msg.subject,
        'content': msg.content,
    }


def init_storage():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def get_msgs(username, older_than=None, newer_than=None, limit=None):
    with session_context() as session:
        query = session.query(Msg).order_by(-Msg.id)

        query = query.filter(Msg.to_user == username)
        if older_than is not None:
            query = query.filter(Msg.id < older_than)

        if newer_than is not None:
            query = query.filter(Msg.id > newer_than)

        if limit:
            query = query.limit(limit)
        return [msg_to_dict(msg) for msg in query.all()]


def send_msg(username, subject, content):
    with session_context() as session:
        msg = Msg(to_user=username, subject=subject, content=content)
        session.add(msg)
        session.flush()
        return msg_to_dict(msg)


def delete_msg(username, msg_id):
    with session_context() as session:
        session.query(Msg).filter(Msg.to_user == username).filter(Msg.id == msg_id).delete()


def delete_old_msgs(username, older_than_id):
    with session_context() as session:
        session.query(Msg).filter(Msg.to_user == username).filter(Msg.id < older_than_id).delete()
