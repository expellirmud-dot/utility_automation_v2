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
COPY deploy/gov_audit /app/deploy/gov_audit
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONPATH=/app
RUN mkdir -p /app/ledger && chown -R appuser:appuser /app
USER appuser
EXPOSE 8001
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import http.client; conn = http.client.HTTPConnection('localhost', 8001); conn.request('GET', '/health'); resp = conn.getresponse(); exit(0 if resp.status == 200 else 1)"
CMD ["uvicorn", "deploy.gov_audit.main:app", "--host", "0.0.0.0", "--port", "8001"]
