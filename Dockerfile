FROM python:3.14-slim AS builder
RUN pip install --no-cache-dir poetry==2.4.1
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.in-project true \
 && poetry install --no-root --only main --no-interaction --no-ansi
COPY gerboise ./gerboise

FROM python:3.14-slim
RUN useradd -u 1000 -m gerboise && mkdir -p /data && chown gerboise:gerboise /data
WORKDIR /app
COPY --from=builder /app/.venv ./.venv
COPY --from=builder /app/gerboise ./gerboise
ENV PATH="/app/.venv/bin:$PATH"
USER gerboise
EXPOSE 8080
VOLUME ["/data"]
CMD ["uvicorn", "gerboise.main:app", "--host", "0.0.0.0", "--port", "8080"]
