import streamlit as st

from requests.exceptions import ConnectionError, HTTPError, Timeout, RequestException

# custom packages
from utils_streamlit import write_impress
from communication import request_backend
from utils_image import save_image, resize_image, base64_to_image
from utils import setup_logging
from config import get_config_from_environment_variables, get_page_title


# Setup logging
@st.cache_data
def get_frontend_config():
    return get_config_from_environment_variables(), setup_logging(__name__)


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
    checkbox_size = 55
    checkbox_background_radius = int(checkbox_size / 6)
    checkbox_label_margin_top = int((checkbox_size / 2))
    st.markdown(f"""
        <style>
            button {{
                min-height: {button_size}px !important;
            }}
            [data-testid="baseButton-primary"] p {{
                font-size: {font_size}px;
            }}
            [data-testid="baseButton-secondary"] p {{
                font-size: {font_size}px;
            }}

            /* checkbox */
            [data-baseweb="checkbox"] [data-testid="stWidgetLabel"] p {{
                /* Styles for the label text for checkbox and toggle */
                font-size: {font_size}px !important;
                width: 200px
            }}

            [data-baseweb="checkbox"] div {{
                /* Styles for the slider container */
                height: {checkbox_size + 2}px;
                width: {4/3 * checkbox_size + 2}px;

            }}
            [data-baseweb="checkbox"] div div {{
                /* Styles for the slider circle */
                height: {checkbox_size}px;
                width: {checkbox_size}px;
            }}

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
            [data-testid="stNotification] p {{ font-size: 16px }}
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
    (camera_info, photo_params, settings_backend, app_settings), logger = get_frontend_config()

    # initialize session state
    if "image" not in st.session_state:
        reset_session_state_image()
    if "show_bboxs" not in st.session_state:
        st.session_state.show_bboxs = False
    if "button_show_boxes_disabled" not in st.session_state:
        st.session_state.button_show_boxes_disabled = True
    if "button_overrule_disabled" not in st.session_state:
        st.session_state.button_overrule_disabled = True

    # content
    if app_settings.title:
        st.title(app_settings.title)
    if app_settings.description:
        st.write(app_settings.description)

    # ----- buttons
    columns = st.columns([1, 3])
    with columns[0]:
        camera_triggered = st.button(
            "Trigger",
            help="trigger camera and call model.",
            type="primary",
            use_container_width=True
        )
        if camera_triggered:
            st.session_state.button_show_boxes_disabled = False

        for _ in range(10):
            st.text("")
        kwargs = {
            "label": "show boxes",
            # "help": "Toggles bounding-boxes.",
            "disabled": st.session_state.button_show_boxes_disabled,
        }

        toggle_boxes = st.toggle(
            **kwargs,
            value=camera_triggered
        )
        # toggle_boxes = st.checkbox(
        #     **kwargs,
        #     value=camera_triggered,
        # )
        if toggle_boxes:
            st.session_state.show_bboxs = not st.session_state.show_bboxs

        overrule_decision = st.button(
            "Overrule decision",
            help="Flags the image as wrongly classified",
            type="secondary",
            disabled=(
                             st.session_state.button_overrule_disabled or st.session_state.image["overruled"]
                     ) and not camera_triggered,
            use_container_width=True
        )

    with columns[1]:
        message_row = st.container()
        # processing
        scores = []
        if camera_triggered:
            reset_session_state_image()

            # call backend
            content = {"images": None, "decision": None, "pattern_name": None, "pattern_lg": None}
            with st.spinner("Call backend to trigger the camera and evaluate the model ..."):
                try:
                    content = request_backend(
                        address=app_settings.address_backend,
                        camera_params=camera_info,
                        photo_params=photo_params,
                        settings=settings_backend,
                        timeout=app_settings.timeout
                    )
                except ConnectionError as ex:
                    logger.error(f"Failed to connect to backend: {ex}")
                    with message_row:
                        st.error(f"Failed to connect to backend.", icon="🚨")
                except Timeout:
                    logger.error(f"Request to backend timed out.")
                    with message_row:
                        st.error(f"Request to backend timed out.", icon="🚨")
                except HTTPError as ex:
                    logger.error(f"An HTTPError occurred when requesting the backend.")
                    with message_row:
                        st.error(f"An HTTPError occurred when requesting the backend.", icon="🚨")
                except RequestException as ex:
                    logger.error(f"A RequestException occurred when requesting the backend: {ex}")
                    with message_row:
                        st.error(f"An error occurred when requesting the backend.", icon="🚨")
                except Exception as ex:
                    logger.error(f"An unexpected error occurred: {ex}")

            # keep image in session state
            images = content["images"]
            if images is not None:
                image = base64_to_image(images["img"])
                st.session_state.image["raw"] = image
                st.session_state.image["show"] = resize_image(image, app_settings.image_size)

                if "img_drawn" in images:
                    img_draw = base64_to_image(images["img_drawn"])
                    st.session_state.image["bboxes"] = resize_image(img_draw, app_settings.image_size)
                    st.session_state.show_bboxs = True
                else:
                    st.session_state.image["bboxes"] = st.session_state.image["show"]

            if "results" in content:
                result = content["results"]
                bboxes, class_ids, scores = result["bboxes"], result["class_ids"], result["scores"]
            else:
                bboxes, class_ids, scores = [], [], []

            st.session_state.image["decision"] = content["decision"]
            st.session_state.image["pattern_name"] = content["pattern_name"]
            st.session_state.image["pattern_lg"] = content["pattern_lg"]

            st.session_state.button_overrule_disabled = False

            # st.rerun()

        # always show decision
        if st.session_state.image["decision"]:
            msg = f"Bounding-Boxes found for pattern {st.session_state.image['pattern_name']}"
            logger.debug(msg)
            with message_row:
                st.success(msg, icon="✅")
        elif st.session_state.image["show"] is not None:
            if st.session_state.image["pattern_lg"] is not None:
                lg = st.session_state.image['pattern_lg']
                msg = (f"Not all objects were found. "
                       f"Best pattern: {st.session_state.image['pattern_name']} with {sum(lg)} / {len(lg)}.")
                logger.warning(msg)
                with message_row:
                    st.error(msg, icon="🚨")
            else:
                with message_row:
                    st.info("No pattern provided to check bounding-boxes.", icon="ℹ️")
                st.session_state.button_overrule_disabled = True

    # show image
        img2show = st.session_state.image["bboxes"] if toggle_boxes else st.session_state.image["show"]
        if img2show is not None:
            st.image(img2show)

    # save image
    if overrule_decision:
        if st.session_state.image["path_to_saved_image"] is None:
            path_to_img = save_image(st.session_state.image["raw"], ".jpg", folder=app_settings.data_folder)
            # keep filename in session state to prevent that the image is saved twice
            st.session_state.image["path_to_saved_image"] = path_to_img

        # make sure that the image is not saved twice
        if overrule_decision:
            st.session_state.image["overruled"] = True
            logger.info(f"Decision overruled for image {st.session_state.image['path_to_saved_image']}.")
            with message_row:
                st.info("Decision was overruled.", icon="ℹ️")

    # impress
    if app_settings.impress:
        write_impress(app_settings.impress)


if __name__ == "__main__":
    main()

    # streamlit run app.py
