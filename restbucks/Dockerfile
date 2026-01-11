FROM python:3.11-slim

WORKDIR /app

# install dependencies
RUN pip install fastapi uvicorn sqlalchemy psycopg2-binary redis

# copy app code
COPY *.py .

# run the app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
