import streamlit as st
import logging
import numpy as np
import sys

# from streamlit_extras.stateful_button import button

# custom packages
from utils_streamlit import write_impress
from utils_communication import trigger_camera, request_model_inference
from utils_image import save_image, bytes_to_image, resize_image
from utils_coordinates import check_boxes
from utils import get_env_variable, cast_logging_level
from config import get_config_from_environment_variables, get_page_title
from plot_pil import plot_bboxs


@st.cache_data
def get_config():
    return get_config_from_environment_variables()


@st.cache_data
def set_css_config():
    # Custom CSS to style the buttons
    font_size = 32

    # --- button
    button_size = 100
    button_padding = int((button_size - font_size) / 2)

    # --- toggle switch
    # toggle_ball_size = 42  # 12px
    # toggle_padding = int(toggle_ball_size / 6)  # 2px
    # toggle_background_border_radius = int(toggle_ball_size / 1.5)  # 8px = 0.5rem
    # toggle_background_height = toggle_ball_size + 2 * toggle_padding  # 16px
    # toggle_background_width = 2 * toggle_background_height  # 32px
    # toggle_ball_translate = toggle_background_width - toggle_ball_size - 2 * toggle_padding  # 16px
    # toggle_label_padding = int((toggle_background_height - font_size) / 2)  # 1px  # half font size

    # --- checkbox
    checkbox_size = 50
    checkbox_background_radius = int(checkbox_size / 6)
    checkbox_label_margin_top = int((checkbox_size / 2))
    logging.debug("Loading CSS styles.")
    st.markdown(f"""
        <style>
            p {{ font-size: {font_size}px; }}
            button {{
                min-height: {button_size}px !important;
            }}
            
            /* checkbox */
            [data-testid="stCheckbox"] label span {{
                /* Styles the checkbox */
                height: {checkbox_size}px;
                width: {checkbox_size}px;
                border-bottom-right-radius: {checkbox_background_radius}px;
                border-bottom-left-radius: {checkbox_background_radius}px;
                border-top-right-radius: {checkbox_background_radius}px;
                border-top-left-radius: {checkbox_background_radius}px;
            }}
            [data-testid="stCheckbox"] span.strut {{width: {0}px;}}
            [data-testid="stCheckbox"] p {{margin-top: {checkbox_label_margin_top}px;}}

        </style>

    """, unsafe_allow_html=True)


def reset_session_state_image():
    st.session_state["image"] = {
        "overruled": False,
        "path_to_saved_image": None,
        "raw": None,
        "show": None,
        "bboxes": None,
        "decision": False,
        "pattern_name": "",
        "pattern_lg": None
    }


def main():
    st.set_page_config(
        page_title=get_page_title(),
        page_icon=":camera:",
        layout="wide"
    )  #:rocket: # must be called as the first Streamlit command in your script.

    set_css_config()

    # load configs
    model_info, camera_info, app_settings = get_config()

    # initialize session state
    if "image" not in st.session_state:
        reset_session_state_image()
    if "show_bboxs" not in st.session_state:
        st.session_state.show_bboxs = False
    if "buttons_disabled" not in st.session_state:
        st.session_state.buttons_disabled = True

    # content
    if app_settings.title:
        st.title(app_settings.title)
    if app_settings.description:
        st.write(app_settings.description)

    # ----- buttons
    columns = st.columns([1, 1, 1, 1])

    with columns[0]:
        camera_triggered = st.button(
            "Trigger",
            help="trigger camera and call model.",
            type="primary",
            use_container_width=True
        )
        if camera_triggered:
            st.session_state.buttons_disabled = False

    with columns[2]:
        kwargs = {
            "label": "show boxes",
            "help": "Toggles bounding-boxes.",
            # "disabled": st.session_state.buttons_disabled,
        }

        # toggle_boxes = st.toggle(
        #     **kwargs,
        #     value=camera_triggered,
        # )
        toggle_boxes = st.checkbox(
            **kwargs,
            value=camera_triggered,
        )
        if toggle_boxes:
            st.session_state.show_bboxs = not st.session_state.show_bboxs

    with columns[3]:
        overrule_decision = st.button(
            "Overrule decision",
            help="Flags the image as wrongly classified",
            type="secondary",
            disabled=st.session_state.buttons_disabled or st.session_state.image["overruled"],
            use_container_width=True
        )

    # processing
    if camera_triggered:
        reset_session_state_image()
        with st.spinner("taking photo ..."):
            try:
                img_raw = trigger_camera(camera_info, timeout=50000)
            except (TimeoutError, ConnectionError):
                st.error("Camera not responding.", icon="🚨")
                logging.error("TimeoutError: trigger_camera(...). Camera not responding.")

        # keep image in session state
        image = bytes_to_image(img_raw)
        st.session_state.image["raw"] = image
        st.session_state.image["show"] = resize_image(image, app_settings.image_size)

        with st.spinner("analyzing model ..."):
            msg = f"main(): request_model_inference({model_info.url}, image_raw={image.size}, extension={camera_info.image_extension})"
            logging.debug(msg)
            try:
                result = request_model_inference(
                    address=model_info.url,
                    image_raw=img_raw,
                    extension=camera_info.image_extension
                )
                logging.debug(f"main(): {result} = request_model_inference(...)")
            except (TimeoutError, ConnectionError):
                st.error("Backend not responding.", icon="🚨")
                logging.error("TimeoutError: request_model_inference(...). Backend not responding.")

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
                logging.debug(f"check_boxes(): {pattern_name}, {lg}")
                st.session_state.image["decision"] = (len(lg) > 1) and all(lg)
                st.session_state.image["pattern_name"] = pattern_name
                st.session_state.image["pattern_lg"] = lg

    if st.session_state.image["decision"]:
        st.success(f"Bounding-Boxes found for pattern {st.session_state.image['pattern_name']}", icon="✅")
    else:
        if app_settings.bbox_pattern is not None:
            st.warning("No pattern to check provided. Result could not be checked.", icon="⚠️")
        elif st.session_state.image["pattern_lg"] is not None:
            msg = f"Not all objects were found. "\
                  f"Best pattern: {st.session_state.image['pattern_name']} with {st.session_state.image['pattern_lg']}."
            logging.warning(msg)
            st.error(msg, icon="🚨")

    # show image
    img2show = st.session_state.image["bboxes"] if toggle_boxes else st.session_state.image["show"]
    if img2show is not None:
        st.image(img2show)

    # save image
    if overrule_decision or (app_settings.save_all_images and camera_triggered):
        if st.session_state.image["path_to_saved_image"] is None:
            path_to_img = save_image(st.session_state.image["raw"], app_settings.data_folder)
            # keep filename in session state to prevent that the image is saved twice
            st.session_state.image["path_to_saved_image"] = path_to_img

        # make sure that the image is not saved twice
        if overrule_decision:
            st.session_state.image["overruled"] = True
            logging.info(f"Decision overruled for image {st.session_state.image['path_to_saved_image']}.")

    # impress
    if app_settings.impress:
        write_impress(app_settings.impress)


if __name__ == "__main__":
    # set logging level
    logging.basicConfig(
        level=cast_logging_level(get_env_variable("LOGGING_LEVEL", logging.DEBUG)),
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            # logging.FileHandler(Path(get_env_variable("LOGFILE", "log")).with_suffix(".log")),
            logging.StreamHandler(sys.stdout)
        ],
    )

    main()

    # streamlit run app.py
# TODO: store files: all, only bad, every xth file
# TODO: add endpoint to get stored files
