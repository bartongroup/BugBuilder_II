# Minimal docker image with python and libraries necessary for download targets
FROM python:3.13-slim

# Set the working directory
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt