FROM python:3.12-slim
WORKDIR /app
COPY configs/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
USER nobody
CMD ["python", "-m", "src.spiders", "all"]
