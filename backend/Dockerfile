FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY nirv ./nirv
COPY paper_session.py demo_session.py ./
RUN mkdir -p /var/lib/nirv && chown -R 10001:10001 /app /var/lib/nirv
USER 10001
EXPOSE 8000
CMD ["uvicorn", "nirv.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
