FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
COPY . .
RUN pip install --no-cache-dir . && useradd --create-home --uid 10001 appuser && mkdir -p /app/uploads/kyc && chown -R appuser:appuser /app
USER 10001:10001
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
