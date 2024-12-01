FROM python:3.12-alpine

ENV PYTHONDONTWRITEBYTECODE 1 \
    PYTHONBUFFERED 1 \ 
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

COPY pyproject.toml poetry.lock ./

RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --only main --no-interaction

WORKDIR /app