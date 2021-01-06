FROM python:3.8-alpine

WORKDIR /usr/src/twicorder

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY python ./python

ENV PYTHONPATH "${PYTONPATH}:/usr/src/twicorder/python"

ENV TC_EXPORT_INPUT_DIR "/data/in"
ENV TC_EXPORT_OUTPUT_DIR "/data/out"
ENV TC_EXPORT_NEW_ONLY "false"
ENV TC_EXPORT_TWEETS_FILTER_FILE ""

CMD [ "python", "./python/twicorder/exporter/controller.py", "tweets" ]
