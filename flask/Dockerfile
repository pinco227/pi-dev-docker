# syntax=docker/dockerfile:1.4
FROM --platform=$BUILDPLATFORM python:3.10-alpine

LABEL MAINTAINER="Paul Istratoaie <p4ul.gg@gmail.com>"

ENV GROUP_ID=1000 \
    USER_ID=1000

WORKDIR /var/www/pi-dev

ADD . /var/www/pi-dev
RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install -r requirements.txt \
    pip3 install gunicorn

RUN addgroup -g $GROUP_ID www
RUN adduser -D -u $USER_ID -G www www -s /bin/sh

USER www

EXPOSE 5000

CMD [ "gunicorn", "-w", "4", "--bind", "0.0.0.0:5000", "wsgi"]