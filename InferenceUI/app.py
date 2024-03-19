import streamlit as st
import numpy as np

from datetime import datetime
from pathlib import Path
import onnxruntime as ort

from utils import get_env_variable
from utils_streamlit import write_impress
from utils_communication import trigger_camera
from utils_image import prepare_image, save_image, scale_coordinates_to_image_size
# from data_models import ModelInfo, CameraInfo, AppSettings
from config import get_config_from_environment_variables
from plot import plot_bboxs


@st.cache_data
def get_config():
    return get_config_from_environment_variables()


def main():
    model_info, camera_info, app_settings = get_config()
    # st.set_page_config(page_title=app_settings.impress.project_name, page_icon=":camera:")  #:rocket: # must be

    # create ONNX session
    if "model_session" not in st.session_state:
        print("DEBUG: load model session")
        st.session_state.model_session = ort.InferenceSession(Path(model_info.path).with_suffix(".onnx"))

    if "overruled" not in st.session_state:
        st.session_state.overruled = False
    if "image_raw" not in st.session_state:
        st.session_state.image_raw = None
    if "image_bboxs" not in st.session_state:
        st.session_state.image_bboxs = None
    if "show_bboxs" not in st.session_state:
        st.session_state.show_bboxs = True

    if app_settings.title:
        st.title("app_settings.title")
    if app_settings.description:
        st.write(app_settings.description)

    # ----- buttons
    columns = st.columns([2, 1, 1])

    with columns[0]:
        camera_triggered = st.button(
            "Trigger",
            help="trigger camera and call model.",
            type="primary"
        )

    with columns[1]:
        toggle_boxes = st.toggle(
            "show boxes",
            value=True,
            help="Toggles bounding-boxes.",
            disabled=not camera_triggered,
            on_change=st.rerun()
        )
        if toggle_boxes:
            st.session_state.show_bboxs = not st.session_state.show_bboxs

    with columns[2]:
        overrule_decision = st.button(
            "Overrule decision",
            help="Flags the image as wrongly classified",
            type="secondary",
            disabled=(not camera_triggered) or st.session_state.overruled
        )

    # processing
    if camera_triggered:
        st.session_state.overruled = False
        with st.spinner("taking photo ..."):
            img = trigger_camera(camera_info)

        with st.spinner("analyzing model ..."):
            # prepare image for evaluation (resize, letterbox, normalize, expand dim, cast to precision, ...)
            img_mdl = prepare_image(img, model_info.image_size, model_info.precision)

            input_name = st.session_state.model_session.get_inputs()[0].name
            output_name = st.session_state.model_session.get_outputs()[0].name
            results = st.session_state.model_session.run([output_name], {input_name: img_mdl})

            bboxes = results[0][:, 1:5]
            class_ids = results[0][:, 5]
            scores = results[0][:, 6]

            # scale boxes
            print(f"DEBUG: img_mdl.shape={img_mdl.shape}, img.shape={img.shape}")
            bboxes = scale_coordinates_to_image_size(bboxes, img_mdl.shape[2:], img.shape[:2])

        # keep image in session state
        st.session_state.image_raw = img

        with st.spinner("draw bounding boxes ..."):
            img_draw = plot_bboxs(
                img,
                bboxes,
                scores,
                class_ids,
                class_map=model_info.class_map,
                color_map=model_info.color_map
            )
            st.session_state.image_bboxs = img_draw
            st.session_state.show_bboxs = True

    # show image
    img2show = st.session_state.image_bboxs if toggle_boxes else st.session_state.image_raw
    if img2show is not None:
        st.image(img2show)

    if overrule_decision:
        save_image(st.session_state.image, app_settings.data_folder)
        # make sure that the image is not saved twice-
        st.session_state.overruled = True

    # impress
    if app_settings.impress:
        write_impress(app_settings.impress)


if __name__ == "__main__":
    # impress = ImpressInfo(
    #     project_name="ToyInference Test",
    #     author="Timo Teststudent",
    #     status="alpha",
    #     date_up_since=datetime.now()
    # )
    # camera_info = CameraInfo(
    #     address="http://localhost:5050/basler/take-photo",
    #     serial_number=24339728,
    #     emulate_camera=True  # for DEBUGGING
    # )
    # model_info = ModelInfo(
    #     path=Path(r"C:\Users\schwmax\Proj\Coding\YOLOv7_scw\trained_models\20240223_CRU_YOLOv7tiny.onnx"),
    #     class_map={0: "a", 1: "b", 2: "c", 3: "d"},
    #     image_size=(640, 640),
    #     precision="fp32"
    # )

    main()

    # streamlit run app.py
# TODO: store files: all, only bad, every xth file
# TODO: add endpoint to get stored files
