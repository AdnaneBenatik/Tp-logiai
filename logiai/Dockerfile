FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY logiai ./logiai

RUN pip install --no-cache-dir .

CMD ["logiai-predict", "--help"]
