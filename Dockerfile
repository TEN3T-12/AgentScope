# 🐍 Base image with Python 3.11
FROM python:3.11-slim

# 🌐 System dependencies
RUN apt-get update && apt-get install -y \
    curl git ffmpeg libsm6 libxext6 \
    && apt-get clean

# 🏗️ Set working directory
WORKDIR /app

# 📋 Copy your code into the container
COPY . /app

# 📦 Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 7860
CMD ["streamlit", "run", "ui/streamlit_app.py", "--server.port", "7860", "--server.address", "0.0.0.0"]
