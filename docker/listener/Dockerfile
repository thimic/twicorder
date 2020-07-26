FROM python:3.8-alpine

WORKDIR /usr/src/twicorder

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY bin ./bin
COPY python ./python

ENV PYTHONPATH "/usr/src/twicorder/python"

ENV TC_STREAM_PROJECT_DIR "/data"
#ENV TC_STREAM_CONFIG_DIR "/config"

CMD [ "python", "./bin/daemon" ]
