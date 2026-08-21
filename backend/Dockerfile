FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY nirv ./nirv
EXPOSE 8000
CMD ["uvicorn", "nirv.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
