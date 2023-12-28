FROM python:3.11.7
LABEL description = "Minseokey's Lablup onboarding"
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENTRYPOINT ["python", "chat_server.py"]