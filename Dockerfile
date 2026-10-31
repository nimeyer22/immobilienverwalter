# syntax=docker/dockerfile:1.7
FROM python:3.12-slim-trixie@sha256:aa943ce411423c7582288f18707ff66eddcbaeb510502d747a72aeb34f30d159

LABEL org.opencontainers.image.source="https://github.com/BitNike/immobilienverwalter"

# Systembibliotheken für WeasyPrint (PDF) und klassische Schriften für die Abrechnung
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 fonts-liberation fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    NK_DATA=/data \
    NK_DOKUMENTE=/dokumente

WORKDIR /app
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --upgrade pip==26.2.2 \
    && pip install -r requirements.txt \
    && pip check

COPY app/ .
RUN useradd --system --uid 1000 nk && mkdir -p /data /dokumente && chown nk /data /dokumente
USER nk

VOLUME ["/data", "/dokumente"]
EXPOSE 8080
# Der Container-Healthcheck prüft nur den Prozess. Orchestratoren verwenden /ready für Traffic.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/live', timeout=4).status == 200 else 1)"]
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "4", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "main:app"]
