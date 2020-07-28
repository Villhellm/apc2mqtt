FROM python:3-alpine
MAINTAINER Villhellm <kind.dragonfruit@gmail.com>

USER root
COPY ./ /src
RUN pip install -r /src/requirements.txt \
    && chown -R 1001:1001 /src

USER 1001
WORKDIR ["/src"]

CMD ["python", "/src/apc2mqtt.py"]
