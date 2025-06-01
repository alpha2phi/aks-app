FROM python:3.10-slim
WORKDIR /app
COPY app.py .
RUN pip install azure-identity azure-keyvault-secrets
CMD ["python", "app.py"]
