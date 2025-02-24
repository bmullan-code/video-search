
FROM python:3.12

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY ./.chromadb/ /app/.chromadb/
COPY ./*.py /app
COPY ./video-search-frontend/build/ /app/video-search-frontend/build/

COPY .env /app/.env
COPY application_default_credentials.json /app

# GOOGLE_APPLICATION_CREDENTIALS
EXPOSE 8000/tcp

# uvicorn.run(app, host="0.0.0.0", port=8000)
CMD ["uvicorn", "service:app","--host", "0.0.0.0","--port","8000"]