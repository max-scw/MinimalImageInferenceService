# syntax=docker/dockerfile:1

# Base Image
FROM python:3.11-slim-bullseye

# Metadata
LABEL author=SCHWMAX
LABEL version=2024.03.06

# Environment variables (default values)
ENV LOGFILE=BaslerAPI

ARG DEBIAN_FRONTEND=noninteractived

# add white-listed websites
RUN printf "deb https://deb.debian.org/debian bullseye main \
            deb https://security.debian.org/debian-security bullseye-security main \
            deb https://deb.debian.org/debian bullseye-updates main" > /etc/apt/sources.list

# new default user
RUN useradd -ms /bin/bash app
# Set the working directory
WORKDIR /home/app


# Install requirements
COPY BaslerAPI/requirements.txt requirements.txt
RUN pip install -r requirements.txt --no-cache-dir

# Copy app into the container
ADD utils ./utils/
COPY BaslerAPI/* ./


# set to non-root user
USER root
RUN chown -R app:app /home/app
USER app

EXPOSE 5050
# FOR DEBUGGING
#ENTRYPOINT ["tail", "-f", "/dev/null"]

ENTRYPOINT ["uvicorn", "main:app", "--host=0.0.0.0", "--port=5050"]

#docker build --tag=basler-api -f=BaslerAPI.Dockerfile .
# docker run -p 3956:3956 -p 46000:46000/udp -p 5001:5000 --name=basler-api-python basler-api