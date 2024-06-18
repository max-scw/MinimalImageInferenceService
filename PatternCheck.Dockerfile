# syntax=docker/dockerfile:1

# Base Image
FROM python:3.11-alpine

# Metadata
LABEL author=SCHWMAX
LABEL version=2024.06.18

# Environment variables (default values)
ENV LOGFILE=PatternCheck

# new default user
#RUN useradd -ms /bin/bash app
# Set the working directory
WORKDIR /home/app
RUN mkdir "data"


# Install requirements
COPY PatternCheck/requirements.txt requirements.txt
RUN pip install -r requirements.txt --no-cache-dir

# Copy app into the container
# 1. copy shated files
ADD utils ./utils/
COPY utils_fastapi.py DataModels.py README.md LICENSE ./
# 2. copy individual files
COPY PatternCheck/main.py PatternCheck/default_config.toml PatternCheck/utils_coordinates.py ./


# set to non-root user
#USER root
#RUN chown -R app:app /home/app
#USER app

EXPOSE 5050

ENTRYPOINT ["uvicorn", "main:app", "--host=0.0.0.0", "--port=5050"]
# FOR DEBUGGING
#ENTRYPOINT ["tail", "-f", "/dev/null"]