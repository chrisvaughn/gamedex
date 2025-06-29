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
COPY migrations/ ./migrations/
COPY alembic.ini ./

# Copy and make startup script executable
COPY start.sh ./
RUN chmod +x start.sh

USER app

EXPOSE 8080
CMD ["./start.sh"]