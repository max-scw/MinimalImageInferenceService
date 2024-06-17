# syntax=docker/dockerfile:1

# Base Image
FROM python:3.11-alpine

# Metadata
LABEL author=SCHWMAX
LABEL version=2024.06.17

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
ADD utils ./utils/
COPY PatternCheck/main.py PatternCheck/default_config.toml ./


# set to non-root user
#USER root
#RUN chown -R app:app /home/app
#USER app

EXPOSE 5050

ENTRYPOINT ["uvicorn", "main:app", "--host=0.0.0.0", "--port=5050"]
# FOR DEBUGGING
#ENTRYPOINT ["tail", "-f", "/dev/null"]