FROM python:3.9-slim-buster

RUN set -ex \
    && apt-get update -y \
    && mkdir /code \
    && groupadd -g 999 appuser \
    && useradd -r -d /code -u 999 -g appuser appuser

WORKDIR /code

COPY . /code

COPY dev_requirements.txt ./dev_requirements.txt

RUN pip install -U pip \
    && pip install -r dev_requirements.txt \
    && chown -R appuser:appuser -R /code

USER appuser

ENTRYPOINT ["python3", "-m", "pytest"]