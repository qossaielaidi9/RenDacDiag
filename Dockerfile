FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt requirements-models.txt ./
RUN pip install --no-cache-dir -r requirements-models.txt
COPY src ./src
COPY config ./config
COPY corpus ./corpus
ENV PYTHONPATH=/app/src
EXPOSE 8000
CMD ["uvicorn", "rendacdiag.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
