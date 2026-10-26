FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN pip install --no-cache-dir 'fastapi>=0.110,<1' 'uvicorn>=0.30,<1' 'cryptography>=42,<47' \
    && groupadd -g 2000 witness \
    && useradd -u 2000 -g 2000 -M -s /usr/sbin/nologin witness \
    && mkdir -p /var/lib/tenir/witness /run/tenir \
    && chown 2000:2000 /var/lib/tenir/witness
COPY witness/ /app/witness/
USER 2000:2000
EXPOSE 8443
