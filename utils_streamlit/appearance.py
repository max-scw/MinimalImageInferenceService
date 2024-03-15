import streamlit as st
import datetime

from .data_models import ImpressInfo


def header(title: str, icon: str = None):
    # configure page => set favicon and page title
    st.set_page_config(page_title=title, page_icon=icon)  # https://emojipedia.org/

    # hide "made with Streamlit" text in footer
    hide_streamlit_style = """
                <style>
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                </style>
                """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)


def write_impress(info: ImpressInfo = None) -> None:
    if info is not None:
        # st.divider()
        with st.expander("Impress"):
            st.text(f"Author: {info.author}")
            st.text(f"Status: {info.status}")
            st.text(f"Up since: {info.date_up_since}")

            if info.additional_info is not None:
                for ky, val in info.additional_info.items():
                    st.text(f"{ky}: {val}")

            st.text(f"Link to project: {info.project_link}")

