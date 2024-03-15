import streamlit as st
import numpy as np

from datetime import datetime
from pathlib import Path
import onnxruntime as ort

from typing import Union, Tuple, List

# from utils.plots import plot_one_box

# from utils_streamlit import ImpressInfo, write_impress
from utils_communication import trigger_camera
from utils_image import prepare_image
from data_models import ModelInfo, CameraInfo


# ----- model
model_session = None
# @st.cache_data
# def load_model(path_to_weights: Path):
#     return ort.InferenceSession(Path(path_to_weights).with_suffix(".onnx"))


def main(
        model_info: ModelInfo,
        camera_info: CameraInfo,
        # impress: ImpressInfo = None
):
    # st.set_page_config(page_title=impress.project_name, page_icon=":rocket")  #:camera:

    # create ONNX session
    global model_session
    if model_session is None:
        # model_session = load_model(model_info.model_path)
        model_session = ort.InferenceSession(Path(model_info.path).with_suffix(".onnx"))

    # st.title("Check assembly of VIAB bearings")
    # st.write("Detecting rolling elements & check correct assembly of each.")
    camera_triggered = st.button("Trigger", help="trigger camera and call model.", type="primary")
    # on_click= callback: trigger camera # FIXME: How to trigger camera?

    if camera_triggered:
        with st.spinner("taking photo ..."):
            img = trigger_camera(camera_info)
        # show image
        placeholder_image = st.image(img, caption=datetime.now().isoformat())

        with st.spinner("analyzing model ..."):
            # prepare image for evaluation (resize, letterbox, normalize, expand dim, cast to precision, ...)
            img_mdl = prepare_image(img, model_info.image_size, model_info.precision)

            input_name = model_session.get_inputs()[0].name
            output_name = model_session.get_outputs()[0].name
            results = model_session.run([output_name], {input_name: img_mdl})
    columns = st.columns([2, 1, 1])

    with columns[1]:
        st.button("Toggle boxes", help="Toggles bounding-boxes.", type="secondary", disabled=not camera_triggered)
    with columns[2]:
        st.button("Overrule decision", help="Flags the image as wrongly classified", type="secondary", disabled=not camera_triggered)

    # impress
    # if impress:
    #     write_impress(impress)


if __name__ == "__main__":
    # impress = ImpressInfo(
    #     project_name="ToyInference Test",
    #     author="Timo Teststudent",
    #     status="alpha",
    #     date_up_since=datetime.now()
    # )
    camera_info = CameraInfo(
        address="http://localhost:5050/basler/take-photo",
        serial_number=24339728,
        emulate_camera=True  # for DEBUGGING
    )
    model_info = ModelInfo(
        path=Path(r"C:\Users\schwmax\Proj\Coding\YOLOv7_scw\trained_models\20240223_CRU_YOLOv7tiny.onnx"),
        class_map={0: "a", 1: "b", 2: "c", 3: "d"},
        image_size=(640, 640),
        precision="fp32"
    )

    main(
        model_info=model_info,
        camera_info=camera_info,
        # impress=impress
    )

    # streamlit run app.py
# TODO: store files: all, only bad, every xth file
# TODO: add endpoint to get stored files
