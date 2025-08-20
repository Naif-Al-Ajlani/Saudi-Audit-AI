FROM registry.access.redhat.com/ubi8/python-39

# Government security baseline
RUN dnf update -y --security && \
    dnf install -y langpacks-ar dejavu-sans-fonts && \
    dnf clean all

# Create non-root user per security policy
RUN useradd -r -u 1001 -g 0 -d /app -s /sbin/nologin aiaudit

# Set Arabic environment
ENV LANG=ar_SA.UTF-8
ENV LC_ALL=ar_SA.UTF-8
ENV TZ=Asia/Riyadh
ENV PYTHONIOENCODING=utf-8

WORKDIR /app

# Copy pre-downloaded wheels (air-gapped)
COPY --chown=1001:0 pip-wheels/ ./pip-wheels/
COPY --chown=1001:0 requirements.txt .
RUN pip install --no-index --find-links ./pip-wheels -r requirements.txt

# Copy application
COPY --chown=1001:0 . .

# Security hardening
RUN chmod -R g=u /app && \
    find /app -type d -exec chmod 755 {} \; && \
    find /app -type f -exec chmod 644 {} \;

USER 1001

# Health check for monitoring
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

EXPOSE 8000

# Performance: use multiple workers
CMD ["uvicorn", "api.endpoints:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]