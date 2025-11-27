FROM python:3.12-slim

WORKDIR /sasalka

COPY ./pyproject.toml ./poetry.lock ./

RUN pip install --no-cache-dir poetry \ 
    && poetry install --no-root

COPY app/ ./app

CMD ["poetry", "run", "python", "app/main.py"]