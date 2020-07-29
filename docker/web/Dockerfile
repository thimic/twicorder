FROM python:3.8-alpine

WORKDIR /usr/src/twicorder

COPY docker/web/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY python ./python

ENV PYTHONPATH "/usr/src/twicorder/python"

ENV TC_WEB_CONFIG "/config"
ENV TC_WEB_DATA "/data"

ENV FLASK_APP "/usr/src/twicorder/python/twicorder/web/browser/main.py"

RUN chmod +x python/twicorder/web/boot.sh

ENTRYPOINT ["./python/twicorder/web/boot.sh"]
