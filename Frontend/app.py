import streamlit as st
import logging

from utils import get_env_variable
from utils_streamlit import write_impress
from utils_communication import trigger_camera, request_model_inference
from utils_image import save_image, bytes_to_image
from config import get_config_from_environment_variables
from plot_pil import plot_bboxs


@st.cache_data
def get_config():
    logging.info("get_config()")
    return get_config_from_environment_variables()


def main():
    # st.set_page_config(page_title=app_settings.impress.project_name, page_icon=":camera:")  #:rocket: # must be

    model_info, camera_info, app_settings = get_config()

    if "overruled" not in st.session_state:
        st.session_state.overruled = False
    if "image_raw" not in st.session_state:
        st.session_state.image_raw = None
    if "image_bboxs" not in st.session_state:
        st.session_state.image_bboxs = None
    if "show_bboxs" not in st.session_state:
        st.session_state.show_bboxs = True
    if "buttons_disabled" not in st.session_state:
        st.session_state.buttons_disabled = True

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
        if camera_triggered:
            st.session_state.buttons_disabled = False

    with columns[1]:
        toggle_boxes = st.toggle(
            "show boxes",
            value=True,
            help="Toggles bounding-boxes.",
            disabled=st.session_state.buttons_disabled
        )
        if toggle_boxes:
            st.session_state.show_bboxs = not st.session_state.show_bboxs

    with columns[2]:
        overrule_decision = st.button(
            "Overrule decision",
            help="Flags the image as wrongly classified",
            type="secondary",
            disabled=st.session_state.buttons_disabled or st.session_state.overruled
        )

    # processing
    if camera_triggered:
        st.session_state.overruled = False
        with st.spinner("taking photo ..."):
            img_raw = trigger_camera(camera_info)

        # keep image in session state
        st.session_state.image_raw = bytes_to_image(img_raw)

        with st.spinner("analyzing model ..."):
            logging.info(f"main(): request_model_inference({model_info.url}), ...)")
            result = request_model_inference(
                address=model_info.url,
                image_raw=img_raw,
                extension=".bmp"
            )

            if isinstance(result, dict):
                bboxes = result["bboxes"]
                class_ids = result["class_ids"]
                scores = result["scores"]
            else:
                bboxes, class_ids, scores = [], [], []

        with st.spinner("draw bounding boxes ..."):
            if bboxes:
                img_draw = plot_bboxs(
                    st.session_state.image_raw.convert("RGB"),
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
        save_image(st.session_state.image_raw, app_settings.data_folder)
        # make sure that the image is not saved twice
        st.session_state.overruled = True

    # impress
    if app_settings.impress:
        write_impress(app_settings.impress)


if __name__ == "__main__":
    main()

    # streamlit run app.py
# TODO: store files: all, only bad, every xth file
# TODO: add endpoint to get stored files
