import json
import shutil
import tempfile
import unittest
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import mailbox_app
from backends import orm, inmemory


@pytest.fixture(params=[
    "SQLAlchemy + SQLite",
    "Python in memory"
])
def storage(request):
    # This does some monkey patching to switch between the backends and to use a temporary db
    if request.param == "SQLAlchemy + SQLite":
        with tempfile.NamedTemporaryFile(suffix=".db") as tempdb:
            tempdb.file.close()
            orm.engine = create_engine("sqlite:///" + tempdb.name, echo=False)
            orm.Session = sessionmaker(bind=orm.engine)
            orm.init_storage()
            yield orm
    elif request.param == "Python in memory":
        yield inmemory
        inmemory.USER_MAILBOXES.clear()
    else:
        assert False, "Unexpected param:" + request.param


@pytest.fixture
def app(storage):
    mailbox_app.storage = storage
    mailbox_app.app.config['TESTING'] = True
    yield mailbox_app.app


@pytest.fixture
def app_client(app):
    with app.test_client() as client:
        yield client


class JsonClient(object):
    def __init__(self, client):
        self.app_client = client

    def forward(self, method, *args, **kwargs):
        json_dict = kwargs.pop('json')
        if json_dict is not None:
            if 'headers' not in kwargs:
                kwargs['headers'] = {}
            kwargs['headers']['content-type'] = 'application/json'
            kwargs['data'] = json.dumps(json_dict)
        return getattr(self.app_client, method)(*args, **kwargs)

    def get(self, *args, **kwargs):
        return self.forward('get', *args, **kwargs)

    def post(self, *args, **kwargs):
        return self.forward('post', *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.forward('delete', *args, **kwargs)


@pytest.fixture
def json_client(app_client):
    return JsonClient(app_client)


def parse_json_rsp(rsp):
    return json.loads(rsp.get_data(as_text=True))


def test_empty(json_client):
    rsp = json_client.get("/msgs", json={"for_user": "test@example.com"})

    assert rsp.status_code == 200
    assert parse_json_rsp(rsp) == []


def test_simple_POST_and_GET(json_client):
    rsp = json_client.post("/msgs", json={
        "for_user": "test@example.com",
        "subject": "my subject",
        "content": "my content",
    })
    assert rsp.status_code == 201
    get_rsp1 = parse_json_rsp(rsp)
    assert get_rsp1['id'] is not None
    assert get_rsp1['subject'] == 'my subject'
    assert get_rsp1['content'] == 'my content'

    rsp = json_client.get("/msgs", json={"for_user": "test@example.com"})
    assert rsp.status_code == 200
    get_rsp2 = parse_json_rsp(rsp)
    assert len(get_rsp2) == 1
    msg = get_rsp2[0]
    assert msg['id'] is not None
    assert msg['subject'] == 'my subject'
    assert msg['content'] == 'my content'


def test_GET_newer_messages(json_client):
    rsp = json_client.post("/msgs", json={
        "for_user": "test@example.com",
        "subject": "msg1",
        "content": "",
    })
    assert rsp.status_code == 201

    rsp = json_client.get("/msgs", json={"for_user": "test@example.com"})
    assert rsp.status_code == 200
    get_rsp1 = parse_json_rsp(rsp)
    assert len(get_rsp1) == 1
    assert get_rsp1[0]['subject'] == 'msg1'

    rsp = json_client.post("/msgs", json={
        "for_user": "test@example.com",
        "subject": "msg2",
        "content": "",
    })
    assert rsp.status_code == 201

    rsp = json_client.get("/msgs", json={"for_user": "test@example.com", "newer_than": get_rsp1[-1]['id']})
    assert rsp.status_code == 200
    get_rsp2 = parse_json_rsp(rsp)
    assert len(get_rsp2) == 1
    msg2 = get_rsp2[0]
    assert msg2['subject'] == 'msg2'


def test_GET_pagination(json_client):
    create_some_msgs(json_client)

    rsp = json_client.get("/msgs", json={"for_user": "test@example.com", "num_msgs": 2})
    assert rsp.status_code == 200
    get_rsp1 = parse_json_rsp(rsp)
    assert get_rsp1[0]['subject'] == 'msg3'
    assert get_rsp1[1]['subject'] == 'msg2'

    last_seen_id = get_rsp1[-1]['id']
    rsp = json_client.get("/msgs", json={"for_user": "test@example.com", "num_msgs": 2, "older_than": last_seen_id})
    assert rsp.status_code == 200
    get_rsp2 = parse_json_rsp(rsp)
    assert len(get_rsp2) == 1
    assert get_rsp2[0]['subject'] == 'msg1'


def test_DELETE_single(json_client):
    create_some_msgs(json_client)

    rsp = json_client.get("/msgs", json={"for_user": "test@example.com"})
    assert rsp.status_code == 200
    get_rsp1 = parse_json_rsp(rsp)
    assert len(get_rsp1) == 3
    assert get_rsp1[0]['subject'] == 'msg3'
    msg2 = get_rsp1[1]
    assert msg2['subject'] == 'msg2'
    assert get_rsp1[2]['subject'] == 'msg1'

    rsp = json_client.delete("/msgs", json={"for_user": "test@example.com", "msg_id": msg2['id']})
    assert rsp.status_code == 204

    rsp = json_client.get("/msgs", json={"for_user": "test@example.com"})
    assert rsp.status_code == 200
    get_rsp1 = parse_json_rsp(rsp)
    assert len(get_rsp1) == 2
    assert get_rsp1[0]['subject'] == 'msg3'
    assert get_rsp1[1]['subject'] == 'msg1'


def test_DELETE_multiple(json_client):
    create_some_msgs(json_client)

    rsp = json_client.get("/msgs", json={"for_user": "test@example.com"})
    assert rsp.status_code == 200
    get_rsp1 = parse_json_rsp(rsp)
    assert len(get_rsp1) == 3
    msg3 = get_rsp1[0]
    assert msg3['subject'] == 'msg3'
    assert get_rsp1[1]['subject'] == 'msg2'
    assert get_rsp1[2]['subject'] == 'msg1'

    rsp = json_client.delete("/msgs", json={"for_user": "test@example.com", "older_than": msg3['id']})
    assert rsp.status_code == 204

    rsp = json_client.get("/msgs", json={"for_user": "test@example.com"})
    assert rsp.status_code == 200
    get_rsp1 = parse_json_rsp(rsp)
    assert len(get_rsp1) == 1
    assert get_rsp1[0]['subject'] == 'msg3'


def create_some_msgs(json_client):
    rsp = json_client.post("/msgs", json={
        "for_user": "test@example.com", "subject": "msg1", "content": "",
    })
    assert rsp.status_code == 201
    rsp = json_client.post("/msgs", json={
        "for_user": "test@example.com", "subject": "msg2", "content": "",
    })
    assert rsp.status_code == 201
    rsp = json_client.post("/msgs", json={
        "for_user": "test@example.com", "subject": "msg3", "content": "",
    })
    assert rsp.status_code == 201
