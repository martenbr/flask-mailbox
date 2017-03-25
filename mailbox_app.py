from collections import defaultdict

from flask import Flask
from flask_restful import reqparse, Api, Resource, abort
import itertools

app = Flask(__name__)
api = Api(app)


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
USER_MAILBOXES['martenbr@example.com'] = Mailbox([
    {'id': 1, 'subject': 'Hello 1', 'content': 'First Message'},
    {'id': 2, 'subject': 'Hello 2', 'content': 'Second Message'},
])

USER_MAILBOXES['test@example.com'] = Mailbox([
    {'id': 1, 'subject': 'Hello', 'content': 'First Message'},
    {'id': 2, 'subject': 'Hello', 'content': 'Second Message'},
    {'id': 3, 'subject': 'Hello', 'content': 'Third Message'},
])

base_parser = reqparse.RequestParser()
base_parser.add_argument('for_user', required=True)

list_request_parser = base_parser.copy()
list_request_parser.add_argument('newer_than', type=int)
list_request_parser.add_argument('older_than', type=int)
list_request_parser.add_argument('num_msgs', type=int)

create_request_parser = base_parser.copy()
create_request_parser.add_argument('subject', type=str, required=True)
create_request_parser.add_argument('content', type=str, required=True)

delete_request_parser = base_parser.copy()
delete_request_parser.add_argument('msg_id', type=int)
delete_request_parser.add_argument('older_than', type=int)


class MsgList(Resource):
    def get(self):
        args = list_request_parser.parse_args(strict=True)
        mailbox = USER_MAILBOXES.get(args.for_user, None)
        if not mailbox:
            return []
        msgs_newest_first = reversed(mailbox.msgs)

        if args.older_than is not None:
            msgs_newest_first = itertools.dropwhile(lambda msg: msg['id'] >= args.older_than, msgs_newest_first)

        if args.newer_than is not None:
            msgs_newest_first = itertools.takewhile(lambda msg: msg['id'] > args.newer_than, msgs_newest_first)

        if args.num_msgs:
            msgs_newest_first = itertools.islice(msgs_newest_first, args.num_msgs)
        return list(msgs_newest_first)

    def post(self):
        args = create_request_parser.parse_args(strict=True)
        mailbox = USER_MAILBOXES[args.for_user]
        msg = mailbox.post_msg(args.subject, args.content)
        return msg, 201

    def delete(self):
        args = delete_request_parser.parse_args(strict=True)
        delete_by_id = args.msg_id is not None
        delete_by_filter = args.older_than is not None
        if delete_by_id and delete_by_filter:
            abort(400, message="Must give only one of msg_id and older_than")
        if delete_by_id:
            mailbox = USER_MAILBOXES.get(args.for_user, None)
            if mailbox:
                for i, msg in enumerate(mailbox.msgs):
                    if msg['id'] == args.msg_id:
                        del mailbox.msgs[i]
                        break
        elif delete_by_filter:
            mailbox = USER_MAILBOXES.get(args.for_user, None)
            if mailbox and mailbox.msgs:
                if mailbox.msgs[-1]['id'] < args.older_than:
                    mailbox.msgs = []
                for i, msg in enumerate(mailbox.msgs):
                    if msg['id'] >= args.older_than:
                        mailbox.msgs = mailbox.msgs[i:]
                        break
        else:
            abort(400, message="Either of msg_id or older_than is required")
        return '', 204


api.add_resource(MsgList, '/msgs')

if __name__ == '__main__':
    app.run(debug=True)
