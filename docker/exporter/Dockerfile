FROM python:3.7-alpine

WORKDIR /usr/src/twicorder

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY python ./python

ENV PYTHONPATH "${PYTONPATH}:/usr/src/twicorder/python"

ENV TC_EXPORT_IN "/data/in"
ENV TC_EXPORT_OUT "/data/out"
ENV TC_EXPORT_NEW_ONLY "true"

CMD [ "python", "./python/twicorder/exporter/controller.py" ]
