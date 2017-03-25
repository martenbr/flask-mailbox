#!/usr/bin/env bash
set -x
# This expects to be run against a fresh DB

# Basic GET and POST
curl http://127.0.0.1:5000/msgs -X GET -d 'for_user=a'
curl http://127.0.0.1:5000/msgs -X POST -d 'for_user=a' -d 'subject=my title' -d 'content='
curl http://127.0.0.1:5000/msgs -X POST -d 'for_user=a' -d 'subject=my title2' -d 'content='
curl http://127.0.0.1:5000/msgs -X GET -d 'for_user=a'

# GET newer messages
curl http://127.0.0.1:5000/msgs -X POST -d 'for_user=a' -d 'subject=my title3' -d 'content='
curl http://127.0.0.1:5000/msgs -X POST -d 'for_user=a' -d 'subject=my title4' -d 'content='
curl http://127.0.0.1:5000/msgs -X GET -d 'for_user=a' -d 'newer_than=2'

# GET with pagination
curl http://127.0.0.1:5000/msgs -X GET -d 'for_user=a' -d 'num_msgs=2'
curl http://127.0.0.1:5000/msgs -X GET -d 'for_user=a' -d 'newer_than=2' -d 'num_msgs=2'

# DELETE one
curl http://127.0.0.1:5000/msgs -X DELETE -d 'for_user=a' -d 'msg_id=3'
curl http://127.0.0.1:5000/msgs -X GET -d 'for_user=a'

# DELETE many
curl http://127.0.0.1:5000/msgs -X DELETE -d 'for_user=a' -d 'older_than=4'
curl http://127.0.0.1:5000/msgs -X GET -d 'for_user=a'
