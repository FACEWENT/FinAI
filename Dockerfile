FROM python:3.12.12-slim

WORKDIR /app
COPY .. .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "app.web:app", "--host", "0.0.0.0", "--port", "8000"]
