import streamlit as st

st.set_page_config(
    page_title="P0 Kab/Kota Pulau Jawa",
    layout="wide",
    initial_sidebar_state="expanded",
)

from dashboard_view import DashboardView  # noqa: E402
from data_loader import DataLoader  # noqa: E402
from model_predictor import ModelPredictor  # noqa: E402
from tema import terapkan_tema  # noqa: E402

terapkan_tema()

view = DashboardView(DataLoader(), ModelPredictor)
halaman = view.tampilkan_sidebar()

if halaman == "Beranda":
    view.tampilkan_beranda()
elif halaman == "Estimasi":
    view.tampilkan_estimasi()
elif halaman == "Kontribusi Variabel":
    view.tampilkan_kontribusi()
else:
    view.tampilkan_informasi()
