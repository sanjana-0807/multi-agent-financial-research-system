# syntax=docker/dockerfile:1
#
# backend/Dockerfile
#
# This image bakes in Tesseract (OCR engine) and Poppler (PDF rasterizer)
# as OS-level packages, so OCR works identically for:
#   - every teammate who runs `docker build` / `docker compose up`
#   - CI pipelines
#   - any cloud host that runs this image (Render, Railway, Fly.io,
#     ECS/Fargate, Azure Container Apps, a plain VM with Docker, etc.)
#
# Nobody downstream needs to manually install Tesseract/Poppler again --
# it's part of the image.
#
# The "# syntax=" line above enables BuildKit cache mounts, which we use
# below so that a flaky/interrupted internet connection doesn't force
# pip to re-download every package from zero on every retry.

FROM python:3.13-slim

# --- System-level dependencies for OCR ---
# tesseract-ocr : the OCR engine itself
# poppler-utils : gives pdf2image the `pdftoppm`/`pdftocairo` binaries
#                 it shells out to for rasterizing PDF pages
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# --- Python dependencies ---
# Copied and installed first (before the rest of the source) so Docker
# can cache this layer -- rebuilds are fast unless requirements.txt
# actually changes.
#
# --mount=type=cache mounts a persistent pip download cache across
# builds (and across retries of THIS build). If your connection drops
# partway through -- like on a large wheel such as lancedb -- the next
# `docker compose up --build` resumes using already-downloaded packages
# from the cache instead of starting from zero.
#
# --timeout / --retries make pip itself more patient with a slow or
# unstable connection before giving up on a single package.
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --timeout 120 --retries 15 -r requirements.txt

# --- Application source ---
COPY . .

# Sanity check baked into the build: fail the image build itself if
# either binary is somehow missing, instead of failing silently later
# at OCR-time in production.
RUN tesseract --version && pdftoppm -v

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]