# BridgeAid FastAPI app image for Cloudflare Containers.
# Must run on linux/amd64. Serves the API + /demo static assets on :8080.
#
# The app resolves data/ and demo/ relative to the source tree
# (loader.py: parents[3] == repo root; main.py: parents[2] == repo root),
# so the container MUST preserve the repo layout: /app/backend/app, /app/data, /app/demo.
FROM python:3.14-slim

# uv for fast, frozen installs (copied from the official uv image).
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_FROZEN=1 \
    # No OS keychain in a Linux container: force the null backend so
    # config.get_secret() falls back cleanly to environment variables.
    PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring

# 1) Install dependencies first (cached layer) from manifests only.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# 2) Copy sources + runtime data, preserving the repo layout.
COPY backend/ backend/
COPY demo/ demo/
COPY data/ data/

# 3) Install the project itself now that its sources exist.
RUN uv sync --frozen --no-dev

EXPOSE 8080
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
