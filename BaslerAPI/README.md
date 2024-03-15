# CameraVision
Provides a Python-based REST API in Docker container to communicate with a Basler camera.

REMARK: on a windows host, Docker Desktop >= 4.19 is required in order to access the Basler camera from a container

## Installation
````
docker build --tag=basler-camera -f Vision_fastAPI.Dockerfile .
````

## Structure
The folder is structured as follows:
```
MetaLearn_Vision  
|- CameraVision
    |- Camera.py <- python code to interact with a Basler camera
    |- main_CameraVision.py  <- fastAPI server to communicate with the Basler camera
    |- pylon_*.deb <- Basler Pylon software suit. The Python package "pypylon" is a wrapper to this software. Installation only required to get full functionality
    |- README.md
    |- requirements.txt  <- pip requirements
    |- Vision_fastAPI.Dockerfile  <- Dockerfile for camera service
```

## Usage
````
docker build --tag=basler/camera -f=Vision
docker run -d -p=5001:5000 -p=3956:3956 -p=46000:46000 --name=basler-camera-python2 basler/camera 
````
docker run -d -p=5001:5000 -p=3956:3956 -p=46000:46000 basler/b

## Authors
Max Schwenzer (SCHWMAX, max.schwenzer@voith.com)

## Project status
active