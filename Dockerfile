FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.6.14 /uv /bin/uv
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN apt-get update && apt-get install -y libpq-dev gcc

WORKDIR /app

COPY pyproject.toml .

RUN uv pip install .
COPY . .

CMD ["python", "main.py"]
