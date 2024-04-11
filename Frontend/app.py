import streamlit as st
import logging
import numpy as np

from utils_streamlit import write_impress
from utils_communication import trigger_camera, request_model_inference
from utils_image import save_image, bytes_to_image, resize_image
from utils_coordinates import check_boxes
from config import get_config_from_environment_variables
from plot_pil import plot_bboxs


@st.cache_data
def get_config():
    return get_config_from_environment_variables()


def reset_session_state_image():
    st.session_state["image"] = {
        "overruled": False,
        "raw": None,
        "show": None,
        "bboxes": None,
        "decision": False,
        "pattern_name": "",
        "pattern_lg": None
    }


def main():
    # st.set_page_config(page_title=app_settings.impress.project_name, page_icon=":camera:")  #:rocket: # must be

    model_info, camera_info, app_settings = get_config()

    if "image" not in st.session_state:
        reset_session_state_image()
    if "show_bboxs" not in st.session_state:
        st.session_state.show_bboxs = True
    if "buttons_disabled" not in st.session_state:
        st.session_state.buttons_disabled = True

    if app_settings.title:
        st.title(app_settings.title)
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
            disabled=st.session_state.buttons_disabled or st.session_state.image["overruled"]
        )

    # processing
    if camera_triggered:
        reset_session_state_image()
        with st.spinner("taking photo ..."):
            img_raw = trigger_camera(camera_info)

        # keep image in session state
        image = bytes_to_image(img_raw)
        st.session_state.image["raw"] = image
        st.session_state.image["show"] = resize_image(image, app_settings.image_size)

        with st.spinner("analyzing model ..."):
            msg = f"main(): request_model_inference({model_info.url}), ...)"
            logging.info(msg)
            print("INFO " + msg)

            result = request_model_inference(
                address=model_info.url,
                image_raw=img_raw,
                extension=camera_info.image_extension
            )
            msg = f"main(): {result} = request_model_inference(...)"
            logging.info(msg)
            print("INFO " + msg)

            if isinstance(result, dict):
                bboxes = result["bboxes"]
                class_ids = result["class_ids"]
                scores = result["scores"]
            else:
                bboxes, class_ids, scores = [], [], []

        with st.spinner("draw bounding boxes ..."):

            if bboxes:
                img_draw = plot_bboxs(
                    st.session_state.image["raw"].convert("RGB"),
                    bboxes,
                    scores,
                    class_ids,
                    class_map=model_info.class_map,
                    color_map=model_info.color_map
                )
                st.session_state.image["bboxes"] = resize_image(img_draw, app_settings.image_size)
                st.session_state.show_bboxs = True
            else:
                st.session_state.image["bboxes"] = st.session_state.image["show"]

        with st.spinner("check bounding boxes ..."):
            if bboxes and (app_settings.bbox_pattern is not None):
                # scale boxes to relative coordinates
                imgsz = img_draw.size
                bboxes_rel = np.array(bboxes) / (imgsz * 2)

                pattern_name, lg = check_boxes(bboxes_rel.tolist(), class_ids, app_settings.bbox_pattern)
                print(f"DEBUG main(): check_boxes(): {pattern_name}, {lg}")
                st.session_state.image["decision"] = (len(lg) > 1) and all(lg)
                st.session_state.image["pattern_name"] = pattern_name
                st.session_state.image["pattern_lg"] = lg

    if st.session_state.image["decision"]:
        st.success(f"Bounding-Boxes found for pattern {st.session_state.image['pattern_name']}", icon="✅")
    else:
        if app_settings.bbox_pattern is not None:
            st.warning("No pattern to check provided. Result could not be checked.", icon="⚠️")
        elif st.session_state.image["pattern_lg"] is not None:
            st.error(
                f"Not all objects were found. "
                f"Best pattern: {st.session_state.image['pattern_name']} with {st.session_state.image['pattern_lg']}.",
                icon="🚨"
            )

    # show image
    img2show = st.session_state.image["bboxes"] if toggle_boxes else st.session_state.image["show"]
    if img2show is not None:
        st.image(img2show)

    if overrule_decision:
        save_image(st.session_state.image["raw"], app_settings.data_folder)
        # make sure that the image is not saved twice
        st.session_state.image["overruled"] = True

    # impress
    if app_settings.impress:
        write_impress(app_settings.impress)


if __name__ == "__main__":
    main()

    # streamlit run app.py
# TODO: store files: all, only bad, every xth file
# TODO: add endpoint to get stored files
