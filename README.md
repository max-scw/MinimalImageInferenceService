# Minimal Image Inference Service

Microservice-based python-app providing an interface for an object recognition project that uses ONNX models.

## Overview

The app consists of 3-4 major building blocks, each wrapped in a Docker container. The graphic below illustrates the microservice system.

![OverviewContainer.png](docs%2FOverviewContainer.png)

- **Backend**: This is the main building block and the entry point if the system is used without a front-end. The [fastAPI](https://fastapi.tiangolo.com/)-based server provides a REST api to send a trigger request to a camera-adapter ([BaslerCameraAdapter](https://github.com/max-scw/BaslerCameraAdapter)); sends the returned image to the Inference server (below); compares the returned result matrix to a given pattern of objects, i.e. the desired locations; and plots the results on the camera image. Both images, the best matching pattern, and an overall good/false decision are returned. Configuration is done via environment variables; default parameters are stored in [Backend > default_config.toml](Backend%2Fdefault_config.toml).
- **Frontend**: Provides a minimalistic user interface (using python's [streamlit](https://streamlit.io/)) to trigger the *Backend*. Displays the camera image incl. bounding-boxes. Configuration is done via environment variables; default parameters are stored in [Frontend > default_config.toml](Frontend%2Fdefault_config.toml).
- **Inference**: Spins-up an [ONNX](https://en.wikipedia.org/wiki/Open_Neural_Network_Exchange)-session for a [fastAPI](https://fastapi.tiangolo.com/)-based server. Mount the onnx-model file to `/home/app/data/` in the container and specify the image size, the precision to which the model was quantized, and the name via the environment variables `MODEL_IMAGE_SIZE` (default *8640, 640)*), `MODEL_PRECISION` (default *fp32*), and `MODEL_FILENAME` (default *model.onnx*) respectively.  See [Inference > default_config.toml](Inference%2Fdefault_config.toml) for details.

The *backend* and *frontend* services allow to specify details for the image acquistition. Note that this only works if a [BaslerCameraAdapter](https://github.com/max-scw/BaslerCameraAdapter)-container is used (or a similar REST interface).
An exemplary configuration provides [docker-compose.yaml](docker-compose.yaml). The docker-compose file further adds a [prometheus](https://prometheus.io/) database and a [grafana](https://grafana.com/) dashboard to provide some monitoring on the app. (The fastAPI-based containers *Backend*, *Interface*, and *BaslerCameraAdapter* expose the standard `\metrics` endpoint for prometheus and specialized counters to monitor the system.)

The frontend provides a minimalistic interface to interact with the backend. Note that it uses streamlits "wide" mode, i.e. landscape mode.

![Example front-end](docs%2Ffrontend.gif)

Note that a container engine facilitates starting all modules, but it is not mandatory. One can run the modules as fastAPI / streamlit server also from different consoles for development purposes.

## Project Structure

````
MinimalImageInferenceService
+-- Backend
  |-- check_boxes.py  # comparing the predicted objects to the desired pattern(s)
  |-- default_config.toml
  |-- main.py  <-- entrypoint for the fastapi-based service
  |-- plot_pil.py  # PIL-based image processing functions
  |-- requirements.txt
  |-- utils_communication.py  # communication to the other endpoints
  |-- utils_data_models.py  # wrapper
+-- docs  # meta data files for the REAMDE (i.e. images)
+-- Frontend
  |-- app.py  <-- entrypoint for the streamlit-based app
  |-- communication.py  # functions to handle the communication to the Backend
  |-- config.py  # wrapping reading the Frontend-specific config
  |-- DataModelsFrontend.py  # pydantic data model for the frontend
  |-- default_config.toml
  |-- entrypoint.sh  # script to assign ownership of a mounted volume to the local non-root user in the Frontend.Docker file
  |-- requirements.txt
+-- Inference
  |-- default_config.toml
  |-- main.py  <-- entrypoint for the fastapi-based service
  |-- requirements.txt
  |-- utils_image_cv2.py # functions for manipulating images using opencv
+-- Monitoring
  +-- grafana
    |-- dashboard.json  # default dashboard
    |-- datasource.yml  # configures prometheus as datas ource so that the dashboard works from start-up
  |-- prometheus.yml  # configuration for promtheus: where and how often to scrape
+-- tools
  |-- determine_desired_coordinates.py  # calculates a bounding-box pattern from labels and predictions
  |-- export_model_predictions.py  # exports the predictions of a given model to a folder (txt + image files with bounding boxes)
  |-- overall_coordinate_evaluation.py  # mock-up to test if the predicted bounding-boxes (of the training set) meet the specified desired-coordinates pattern
  |-- rotate_bbox.py  # helper function to batch rotate boxes
+-- utils  # shared standard functions to read environment variables or the config
+-- utils_streamlit  # standard functions for streamlit (only used in Frontend)
|-- Backend.Dockerfile
|-- DataModels.py  # shared pydantic data model
|-- DataModels_BaslerCameraAdapter.py  # shared pydantic data model (take from https://github.com/max-scw/BaslerCameraAdapter)
|-- docker-compose.yaml  # <-- use this file for an exemplary start-up of the app
|-- Frontend.Dockerfile
|-- Inference.Dockerfile
|-- LICENSE
|-- README.md
|-- utils_config.py  # shared helper functions
|-- utils_fastapi.py  # shared helper functions
|-- utils_image.py  # shared helper functions
````

## Quick Start

Use a container engine such as Docker and the compose plugin to spin up the app automatically with `docker-compose up -d`

If you want to use bare Python (without a container engine), I recommend using Python 3.11 (or later).
Set up a virtual environment installing all requirements: [Backend > requirements.txt](Backend%2Frequirements.txt), [Frontend > requirements.txt](Frontend%2Frequirements.txt), and [Inference > requirements.txt](Inference%2Frequirements.txt).

````shell
python venv .venv  # create virtual environment
source ./.venv/bin/activate  # activate virtual environment (linux)
pip install -r Backend/requirements.txt -r Frontend/requirements.txt -r Inference/requirements.txt  # install requirements
````

Now you have a virtual environment (i.e. all Python-packages are stored to the hidden folder .venv in this directory.)

Start the fastAPI-based servers just by executing the *main.py* files; for the streamlit-based Frontend call `streamlit run app.py` in [Frontend](Frontend) in separate consoles. Note that you will certainly have to copy some shared files an packages to the sub-folders in order to start all servers without a container engine.


## Docker

Find the corresponding released containers on dockerhub:

- [backend](https://hub.docker.com/repository/docker/maxscw/minimal-image-inference-backend/)
- [frontend](https://hub.docker.com/repository/docker/maxscw/minimal-image-inference-frontend/)
- [inference engine](https://hub.docker.com/repository/docker/maxscw/minimal-image-inference-engine/)

See the [docker-compose.yaml](docker-compose.yaml) file for an example how to start the app with all three major containers.
Add [prometheus](https://prometheus.io/) and [grafana](https://grafana.com/) optionally to monitor the containers.


## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Author

 - max-scw
