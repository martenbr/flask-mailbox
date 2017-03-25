import itertools
from collections import defaultdict


class Mailbox(object):
    def __init__(self, msgs=None):
        if msgs:
            self.lastId = msgs[-1]['id']
            self.msgs = msgs
        else:
            self.lastId = 0
            self.msgs = []

    def post_msg(self, subject, content):
        self.lastId += 1
        msg = {
            'id': self.lastId,
            'subject': subject,
            'content': content,
        }
        self.msgs.append(msg)
        return msg


USER_MAILBOXES = defaultdict(Mailbox)


def init_storage():
    pass


def get_msgs(username, older_than=None, newer_than=None, limit=None):
    mailbox = USER_MAILBOXES.get(username, None)
    if not mailbox:
        return []
    msgs_newest_first = reversed(mailbox.msgs)

    if older_than is not None:
        msgs_newest_first = itertools.dropwhile(lambda msg: msg['id'] >= older_than, msgs_newest_first)

    if newer_than is not None:
        msgs_newest_first = itertools.takewhile(lambda msg: msg['id'] > newer_than, msgs_newest_first)

    if limit:
        msgs_newest_first = itertools.islice(msgs_newest_first, limit)
    return list(msgs_newest_first)


def send_msg(username, subject, content):
    mailbox = USER_MAILBOXES[username]
    msg = mailbox.post_msg(subject, content)
    return msg


def delete_msg(username, msg_id):
    mailbox = USER_MAILBOXES.get(username, None)
    if mailbox:
        for i, msg in enumerate(mailbox.msgs):
            if msg['id'] == msg_id:
                del mailbox.msgs[i]
                break


def delete_old_msgs(username, older_than_id):
    mailbox = USER_MAILBOXES.get(username, None)
    if mailbox and mailbox.msgs:
        if mailbox.msgs[-1]['id'] < older_than_id:
            mailbox.msgs = []
        for i, msg in enumerate(mailbox.msgs):
            if msg['id'] >= older_than_id:
                mailbox.msgs = mailbox.msgs[i:]
                break
