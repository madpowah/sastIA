FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    git \
    ca-certificates \
    curl \
    && install -m 0755 -d /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc \
    && chmod a+r /etc/apt/keyrings/docker.asc \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian bookworm stable" > /etc/apt/sources.list.d/docker.list \
    && apt-get update && apt-get install -y docker-ce-cli \
    && rm -rf /var/lib/apt/lists/* \
    && addgroup --system --gid 1001 sastia \
    && adduser --system --uid 1001 --ingroup sastia --no-create-home sastia \
    && addgroup --system docker \
    && adduser sastia docker

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chown -R sastia:sastia /app && chmod -R 755 /app

EXPOSE 9000

USER sastia

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000"]
