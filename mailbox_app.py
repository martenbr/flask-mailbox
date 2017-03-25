from flask import Flask
from flask_restful import reqparse, Api, Resource, abort
from backends import orm

storage = orm

app = Flask(__name__)
api = Api(app)

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
        msgs = storage.get_msgs(args.for_user,
                                older_than=args.older_than,
                                newer_than=args.newer_than,
                                limit=args.num_msgs)
        return msgs

    def post(self):
        args = create_request_parser.parse_args(strict=True)
        msg = storage.send_msg(args.for_user, args.subject, args.content)
        return msg, 201

    def delete(self):
        args = delete_request_parser.parse_args(strict=True)
        delete_by_id = args.msg_id is not None
        delete_by_filter = args.older_than is not None
        if delete_by_id and delete_by_filter:
            abort(400, message="Must give only one of msg_id and older_than")
        if delete_by_id:
            storage.delete_msg(args.for_user, args.msg_id)
        elif delete_by_filter:
            storage.delete_old_msgs(args.for_user, older_than_id=args.older_than)
        else:
            abort(400, message="Either of msg_id or older_than is required")
        return '', 204


api.add_resource(MsgList, '/msgs')

if __name__ == '__main__':
    app.before_first_request(storage.init_storage)
    app.run(debug=True)
