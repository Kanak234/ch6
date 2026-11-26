# Google Cloud Run image (optional — the app also runs on Streamlit Community Cloud).
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py ./
COPY saans ./saans
COPY assets ./assets
COPY .streamlit/config.toml ./.streamlit/config.toml
# Run as a non-root user (least privilege).
RUN useradd --create-home appuser
USER appuser
# Cloud Run injects $PORT; keys come from Secret Manager as env vars, never baked into the image.
CMD ["sh", "-c", "streamlit run app.py --server.port=${PORT:-8080} --server.address=0.0.0.0"]
