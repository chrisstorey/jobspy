FROM python:3.13-slim

WORKDIR /app
# RUN apk --no-cache add curl
# RUN apk add --update coreutils && rm -rf /var/cache/apk/*

COPY main.py /app/
COPY .env_copy /app/.env
COPY requirements.txt /app/

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    coreutils \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt
RUN chmod +x /app/main.py
RUN mkdir -p /app/data

CMD ["python", "/app/main.py"]
