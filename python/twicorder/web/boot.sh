#!/bin/sh
flask db upgrade -d python/twicorder/web/migrations
exec gunicorn -b :5000 --access-logfile - --error-logfile - twicorder.web.browser.main:app