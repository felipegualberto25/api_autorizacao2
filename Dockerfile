FROM python:3.10-slim-bullseye

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# -------------------------------------------------
# Dependências de sistema
# -------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    curl \
    wget \
    ca-certificates \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libgtk2.0-dev \
    libatlas-base-dev \
    libopenblas-dev \
    libomp-dev \
    gfortran \
    pkg-config \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# -------------------------------------------------
# Tooling Python
# -------------------------------------------------
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# -------------------------------------------------
# NumPy FIXADO (ABI compatível)
# -------------------------------------------------
RUN pip install --no-cache-dir numpy==1.26.4

# -------------------------------------------------
# OpenCV FIXADO (HEADLESS, compatível com numpy 1.26)
# -------------------------------------------------
RUN pip install --no-cache-dir opencv-python-headless==4.9.0.80

# -------------------------------------------------
# Torch CPU (compatível)
# -------------------------------------------------
RUN pip install --no-cache-dir torch torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cpu

# -------------------------------------------------
# EasyOCR (agora não quebra mais)
# -------------------------------------------------
RUN pip install --no-cache-dir easyocr

# -------------------------------------------------
# FAISS + Embeddings
# -------------------------------------------------
RUN pip install --no-cache-dir faiss-cpu==1.8.0
RUN pip install --no-cache-dir sentence-transformers

# -------------------------------------------------
# Outras libs
# -------------------------------------------------
RUN pip install --no-cache-dir pandas

# -------------------------------------------------
# Requirements do projeto (SEM numpy, SEM opencv, SEM torch)
# -------------------------------------------------
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# -------------------------------------------------
# Código
# -------------------------------------------------
COPY . /app

RUN mkdir -p /app/data /app/data/vector_index && chmod -R 755 /app/data
RUN mkdir -p /app/data/logs

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.api:app --host 0.0.0.0 --port 8000"]
