import streamlit as st
from pathlib import Path
from PIL import Image


@st.cache_data
def read_image(path_to_image: Path) -> Image:
    return Image.open(path_to_image)
