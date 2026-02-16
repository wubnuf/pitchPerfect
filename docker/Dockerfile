# docker/Dockerfile
FROM python:3.9-slim

# Install system dependencies for OCR, OpenCV, and pyautogui
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    libssl-dev \
    wget \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# Install libGL for OpenCV
RUN apt-get update && \
    apt-get install -y libgl1-mesa-glx && \
    rm -rf /var/lib/apt/lists/*

# Install X11 and scrot for pyautogui screenshot support
RUN apt-get update && apt-get install -y \
    scrot \
    python3-tk \
    python3-dev \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Make work directory
WORKDIR /app
COPY app/requirements.txt requirements.txt

COPY .env .env

# Install compatible numpy and other dependencies from requirements.txt
RUN pip install --no-cache-dir numpy==1.21.6
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ /app/

# Download spaCy English model
RUN python -m spacy download en_core_web_sm

EXPOSE 8000

CMD ["python", "main.py"]
