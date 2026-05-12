FROM python:3.12-slim as builder
WORKDIR /app
COPY deploy/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
RUN groupadd -r appuser && useradd -r -g appuser appuser
COPY --from=builder /root/.local /home/appuser/.local
COPY src /app/src
COPY deploy/shared /app/deploy/shared
COPY deploy/gov_identity /app/deploy/gov_identity
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONPATH=/app
RUN chown -R appuser:appuser /app
USER appuser
EXPOSE 8002
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import http.client; conn = http.client.HTTPConnection('localhost', 8002); conn.request('GET', '/health'); resp = conn.getresponse(); exit(0 if resp.status == 200 else 1)"
CMD ["uvicorn", "deploy.gov_identity.main:app", "--host", "0.0.0.0", "--port", "8002"]
