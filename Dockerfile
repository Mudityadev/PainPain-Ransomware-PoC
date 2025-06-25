FROM python:3.10-slim

# Install system dependencies for GUI
RUN apt-get update && \
    apt-get install -y python3-tk xauth x11-apps && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set environment variables for GUI (X11)
ENV DISPLAY=:0

CMD ["python", "main.py", "-e", "-p", "./testDir/banking_samples"] 