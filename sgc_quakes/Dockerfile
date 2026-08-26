ARG BUILD_FROM=ghcr.io/home-assistant/alpine:3.19
FROM ${BUILD_FROM}

ENV LANG=C.UTF-8 \
    PYTHONUNBUFFERED=1

RUN apk add --no-cache \
    python3 \
    py3-pip \
    py3-requests

WORKDIR /data

COPY run.sh /run.sh
COPY app.py /app.py

RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
