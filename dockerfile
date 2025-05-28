# Use a base image that includes Miniconda3 and common dependencies
FROM continuumio/miniconda3:latest

# Install additional system-level dependencies
RUN apt-get update && \
    apt-get install -y --fix-missing --no-install-recommends \
    build-essential \
    cmake gcc g++ git python3-dev nodejs npm\
    libblas-dev \
    && apt-get clean curl unzip&& \
    rm -rf /var/lib/apt/lists/*

# Initialize conda for bash shell and source ~/.bashrc to apply the changes
RUN echo "conda init bash" >> ~/.bashrc && \
    echo "source ~/.bashrc" >> ~/.bashrc
    
# Set the default shell to bash
SHELL ["/bin/sh", "--login", "-c"]