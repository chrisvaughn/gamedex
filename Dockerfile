FROM python:3.13-alpine

ENV PYTHONUNBUFFERED=1 \ 
    PYTHONDONTWRITEBYTECODE=1 

# Create non-root user
RUN adduser -D app

RUN pip install poetry && poetry config virtualenvs.in-project true

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry install --without dev

COPY app/ ./app/

USER app

ENV HOST=0.0.0.0 PORT=8080
EXPOSE ${PORT}
CMD ["uvicorn", "app.main:app", "--host", "${HOST}", "--port", "${PORT}"]