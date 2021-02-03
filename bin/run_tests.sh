#!/bin/bash

cp robobroker/db.sqlite3 robobroker/test.db.sqlite3
python manage.py test --pattern "*_tests.py" -v 2
rm -f robobroker/test.db.sqlite3
