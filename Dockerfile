FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
COPY vendor /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt
COPY . .
ENV PYTHONUNBUFFERED=1 FLASK_HOST=0.0.0.0
EXPOSE 5000
CMD ["python", "demo/app.py"]
