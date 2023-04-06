FROM python:3.10-slim as builder

ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=1.4.1

WORKDIR /app
COPY . /app/

RUN pip install "poetry==${POETRY_VERSION}" && \
    apt update && \
    apt install -y curl && \
    curl -sSL https://r.mariadb.com/downloads/mariadb_repo_setup > ./mariadb_repo_setup && \
    echo "ad125f01bada12a1ba2f9986a21c59d2cccbe8d584e7f55079ecbeb7f43a4da4  mariadb_repo_setup" | sha256sum -c - && \
    chmod +x mariadb_repo_setup && \
    ./mariadb_repo_setup --mariadb-server-version="mariadb-10.6" && \
    apt install -y libmariadb3 libmariadb-dev build-essential && \
    rm mariadb_repo_setup && \
    apt purge -y curl && \
    poetry install --no-interaction --no-ansi --without dev

ENTRYPOINT [ "poetry", "run", "python3", "/app/main.py" ]