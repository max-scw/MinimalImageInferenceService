# syntax=docker/dockerfile:1

# Base Image
FROM python:3.11-slim-bullseye as base
ENV PYTHONUNBUFFERED 1

# Metadata
LABEL author=SCHWMAX
LABEL version=2024.03.07

# Environment variables (default values)
ENV LOGFILE=ToyInference

ARG DEBIAN_FRONTEND=noninteractived

RUN printf "deb https://deb.debian.org/debian bullseye main \
    deb https://security.debian.org/debian-security bullseye-security main \
    deb https://deb.debian.org/debian bullseye-updates main" > /etc/apt/sources.list


# new default user
RUN useradd -ms /bin/bash app
# Set the working directory
WORKDIR /home/app
RUN mkdir ./data
# mount onnx model to /home/app/model.onnx or /home/app/data/model.onnx


# Install requirements
COPY InferenceUI/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt --no-cache-dir

# Copy app into the container
ADD utils ./utils/
ADD utils_streamlit ./utils_streamlit/
COPY InferenceUI/* ./


# set to non-root user
USER root
RUN chown -R app:app /home/app
USER app

# Define the health check using curl for both HTTP and HTTPS
HEALTHCHECK --interval=30s --timeout=5s \
  CMD (curl -fsk http://localhost:8501/_stcore/health) || (curl -fsk https://localhost:8501/_stcore/health) || exit 1#

# Expose the ports
EXPOSE 8501

## Start the app
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
#ENTRYPOINT ["tail", "-f", "/dev/null"]

