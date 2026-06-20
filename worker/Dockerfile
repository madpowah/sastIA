FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && addgroup --system --gid 1001 sastia \
    && adduser --system --uid 1001 --ingroup sastia --no-create-home sastia

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chown -R sastia:sastia /app && chmod -R 755 /app

EXPOSE 9000

USER sastia

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000"]
