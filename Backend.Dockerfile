# syntax=docker/dockerfile:1

# Base Image
FROM python:3.11-slim-bullseye

# Metadata
LABEL author=SCHWMAX
LABEL version=2024.06.17

# Environment variables (default values)
ENV LOGFILE=Backend

ARG DEBIAN_FRONTEND=noninteractived

# add white-listed websites
RUN printf "deb https://deb.debian.org/debian bullseye main \
            deb https://security.debian.org/debian-security bullseye-security main \
            deb https://deb.debian.org/debian bullseye-updates main" > /etc/apt/sources.list

# new default user
RUN useradd -ms /bin/bash app
# Set the working directory
WORKDIR /home/app
RUN mkdir "data"


# Install requirements
COPY Backend/requirements.txt requirements.txt
RUN pip install -r requirements.txt --no-cache-dir

# Copy app into the container
# 1. copy shated files
ADD utils ./utils/
COPY utils_fastapi.py DataModels.py ./
# 2. copy individual files
COPY Backend/main.py Backend/default_config.toml ./


# set to non-root user
USER root
RUN chown -R app:app /home/app
USER app

EXPOSE 5050

ENTRYPOINT ["uvicorn", "main:app", "--host=0.0.0.0", "--port=5050"]
# FOR DEBUGGING
#ENTRYPOINT ["tail", "-f", "/dev/null"]