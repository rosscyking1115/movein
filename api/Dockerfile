# UK Housing Decision Support API — small FastAPI service that ships the slim
# read-only decision extract and serves it from memory.
FROM python:3.13-slim

WORKDIR /srv

COPY api/requirements.txt ./api/requirements.txt
RUN pip install --no-cache-dir -r api/requirements.txt

COPY api ./api
COPY data/decision.duckdb ./data/decision.duckdb

EXPOSE 8080
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080"]
