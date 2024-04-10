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
ADD utils ./utils/
ADD utils_streamlit ./utils_streamlit/
COPY Frontend/* ./


# set to non-root user
USER root
RUN chown -R appuser:appuser /home/app
USER appuser

# Define the health check using curl for both HTTP and HTTPS
HEALTHCHECK --interval=30s --timeout=5s \
  CMD (curl -fsk http://localhost:8501/_stcore/health) || (curl -fsk https://localhost:8501/_stcore/health) || exit 1#

# Expose the ports
EXPOSE 8501

## Start the app
# Copy the entrypoint script into the container
COPY Frontend/entrypoint.sh /usr/local/bin/entrypoint.sh

# Set execute permissions for the entrypoint script
RUN chmod +x /usr/local/bin/entrypoint.sh

# Set the entrypoint script as the entrypoint for the container
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
#CMD ["tail", "-f", "/dev/null"]

