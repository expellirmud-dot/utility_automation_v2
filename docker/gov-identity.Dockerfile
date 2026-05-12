FROM python:3.12-slim as builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

RUN useradd -m appuser
USER appuser

EXPOSE 8002
CMD ["uvicorn", "src.services.auth.api.gov_identity_app:app", "--host", "0.0.0.0", "--port", "8002"]
