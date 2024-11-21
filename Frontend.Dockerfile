# syntax=docker/dockerfile:1

# Base Image
FROM python:3.11-slim-bullseye as base
ENV PYTHONUNBUFFERED 1

# Metadata
LABEL author=SCHWMAX
LABEL version=2024.03.19

# Environment variables (default values)
ENV LOGFILE=ToyInferenceFrontend

ARG DEBIAN_FRONTEND=noninteractived

RUN printf "deb https://deb.debian.org/debian bullseye main \
    deb https://security.debian.org/debian-security bullseye-security main \
    deb https://deb.debian.org/debian bullseye-updates main" > /etc/apt/sources.list


# new default user
RUN useradd -ms /bin/bash appuser
# Set the working directory
WORKDIR /home/app
RUN mkdir ./data
# mount onnx model to /home/app/model.onnx or /home/app/data/model.onnx


# Install requirements
COPY Frontend/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt --no-cache-dir

# Copy app into the container
# 1. copy shated files
ADD utils ./utils/
COPY utils_fastapi.py \
     utils_image.py \
     DataModels.py \
     DataModels_BaslerCameraAdapter.py \
     utils_config.py  \
     README.md \
     LICENSE \
     ./
# 2. copy individual files
ADD /utils_streamlit ./utils_streamlit/
COPY Frontend/app.py \
     Frontend/communication.py \
     Frontend/config.py \
     Frontend/DataModelsFrontend.py \
     Frontend/default_config.toml \
     ./


# Expose the ports
EXPOSE 8501

# Define the health check using curl for both HTTP and HTTPS
HEALTHCHECK --interval=30s --timeout=5s \
  CMD (curl -fsk http://localhost:8501/_stcore/health) || (curl -fsk https://localhost:8501/_stcore/health) || exit 1

## Start the app
# Copy the entrypoint script into the container
COPY Frontend/entrypoint.sh /usr/local/bin/entrypoint.sh

# Set execute permissions for the entrypoint script
RUN chmod +x /usr/local/bin/entrypoint.sh

# set to non-root user
USER root
RUN chown -R appuser:appuser /home/app
USER appuser

# Set the entrypoint script as the entrypoint for the container
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
#CMD ["tail", "-f", "/dev/null"]

