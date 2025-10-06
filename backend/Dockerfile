# Use an official Python runtime as a parent image
FROM nvcr.io/nvidia/pytorch:24.05-py3

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
# COPY . . <-- skipping for development purposes, mounted volume via docker-compose

# Install system dependencies for CUDA and other tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        wget \
        build-essential \
        git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install torch torchvision torchaudio 

# Install additional Python dependencies
RUN pip install packaging ninja wheel setuptools setuptools-scm flash-attn

# Clone and install FlashAttention from GitHub
RUN git clone https://github.com/Dao-AILab/flash-attention.git && \
    cd flash-attention/hopper && \
    python setup.py install

# Install project dependencies
RUN pip install -r requirements.txt
# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]