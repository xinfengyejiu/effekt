FROM xxx:xxx/library/python:3.10-bookworm

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN mkdir -p /app/logs

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5010

CMD ["gunicorn", "--config=gunicorn.conf.py", "manage:app"]
