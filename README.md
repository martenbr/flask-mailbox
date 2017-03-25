# Flask-Mailbox
This is a small sample application with a REST API for sending messages.
This application requires Python3 and it is recommended to run run it using virtualenv:

    virtualenv ~/flaskvirtualenv -p python3
    ~/flaskvirtualenv/bin/pip install -r requirements.txt
    ~/flaskvirtualenv/bin/python3 mailbox_app.py
    
To run the tests execute:

    ~/flaskvirtualenv/bin/py.test api_tests.py -v

The file [curl_examples.sh](curl_examples.sh) contains some example CURL usages against the application,
here is a sample execution of that script:

    $ bash curl_examples.sh 
    + curl http://127.0.0.1:5000/msgs -X GET -d for_user=a
    []
    + curl http://127.0.0.1:5000/msgs -X POST -d for_user=a -d 'subject=my title' -d content=
    {
        "content": "",
        "id": 1,
        "subject": "my title"
    }
    + curl http://127.0.0.1:5000/msgs -X POST -d for_user=a -d 'subject=my title2' -d content=
    {
        "content": "",
        "id": 2,
        "subject": "my title2"
    }
    + curl http://127.0.0.1:5000/msgs -X GET -d for_user=a
    [
        {
            "content": "",
            "id": 2,
            "subject": "my title2"
        },
        {
            "content": "",
            "id": 1,
            "subject": "my title"
        }
    ]
    + curl http://127.0.0.1:5000/msgs -X POST -d for_user=a -d 'subject=my title3' -d content=
    {
        "content": "",
        "id": 3,
        "subject": "my title3"
    }
    + curl http://127.0.0.1:5000/msgs -X POST -d for_user=a -d 'subject=my title4' -d content=
    {
        "content": "",
        "id": 4,
        "subject": "my title4"
    }
    + curl http://127.0.0.1:5000/msgs -X GET -d for_user=a -d newer_than=2
    [
        {
            "content": "",
            "id": 4,
            "subject": "my title4"
        },
        {
            "content": "",
            "id": 3,
            "subject": "my title3"
        }
    ]
    + curl http://127.0.0.1:5000/msgs -X GET -d for_user=a -d num_msgs=2
    [
        {
            "content": "",
            "id": 4,
            "subject": "my title4"
        },
        {
            "content": "",
            "id": 3,
            "subject": "my title3"
        }
    ]
    + curl http://127.0.0.1:5000/msgs -X GET -d for_user=a -d newer_than=2 -d num_msgs=2
    [
        {
            "content": "",
            "id": 4,
            "subject": "my title4"
        },
        {
            "content": "",
            "id": 3,
            "subject": "my title3"
        }
    ]
    + curl http://127.0.0.1:5000/msgs -X DELETE -d for_user=a -d msg_id=3
    + curl http://127.0.0.1:5000/msgs -X GET -d for_user=a
    [
        {
            "content": "",
            "id": 4,
            "subject": "my title4"
        },
        {
            "content": "",
            "id": 2,
            "subject": "my title2"
        },
        {
            "content": "",
            "id": 1,
            "subject": "my title"
        }
    ]
    + curl http://127.0.0.1:5000/msgs -X DELETE -d for_user=a -d older_than=4
    + curl http://127.0.0.1:5000/msgs -X GET -d for_user=a
    [
        {
            "content": "",
            "id": 4,
            "subject": "my title4"
        }
    ]

