FROM python:3.9.6-slim-buster

RUN pip install poetry==1.1.13

# Configuring poetry
RUN poetry config virtualenvs.create false

# Copying requirements of a project
COPY pyproject.toml poetry.lock /app/src/
WORKDIR /app/src

# Installing requirements
RUN poetry install

# Copying actuall application
COPY . /app/src/
RUN poetry install

RUN mkdir /db_data
RUN touch /db_data/db.sqlite3

CMD ["/usr/local/bin/python", "-m", "kucoin_manager"]
