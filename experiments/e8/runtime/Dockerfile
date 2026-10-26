FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN pip install --no-cache-dir 'cryptography>=42,<47' 'httpx>=0.27,<1' \
    && groupadd -g 1000 runtime \
    && useradd -u 1000 -g 1000 -M -s /usr/sbin/nologin runtime \
    && mkdir -p /var/lib/tenir/runtime /etc/tenir-witness \
    && chown 1000:1000 /var/lib/tenir/runtime
COPY witness/ /app/witness/
COPY runtime/ /app/runtime/
USER 1000:1000
CMD ["sleep", "infinity"]
