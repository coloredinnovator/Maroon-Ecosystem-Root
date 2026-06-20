FROM python:3.12-slim
WORKDIR /app
COPY configs/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
EXPOSE 8007
USER nobody
CMD ["uvicorn", "src.rtm:app", "--host", "0.0.0.0", "--port", "8007"]
