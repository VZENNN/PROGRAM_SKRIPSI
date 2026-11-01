import pickle
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from catboost import Pool

from data_loader import FITUR, ROOT


@dataclass
class HasilEstimasi:
    estimasi: float
    nilai_dasar: float      # rata-rata prediksi model (titik awal SHAP)
    shap: dict              # {fitur: kontribusi}, jumlahnya + nilai_dasar = estimasi


@st.cache_resource(show_spinner="Memuat model CatBoost…")
def _muat_semua(folder):
    folder = Path(folder)
    model = {}
    for nama in ("gabungan", "kabupaten", "kota"):
        with open(folder / f"model_{nama}.pkl", "rb") as f:
            model[nama] = pickle.load(f)
    with open(folder / "model_per_kabkota.pkl", "rb") as f:
        per_wilayah = pickle.load(f)  # dict {kode_kabkota: CatBoostRegressor}
    return model, per_wilayah


@st.cache_data(show_spinner="Menghitung nilai SHAP…")
def _shap_panel(_model, nama_model, X):
    """Nilai SHAP per baris; nama_model hanya sebagai kunci cache (_model tidak di-hash)."""
    sv = _model.get_feature_importance(Pool(X[FITUR]), type="ShapValues")
    return pd.DataFrame(sv[:, :-1], columns=[f"shap_{f}" for f in FITUR], index=X.index)


class ModelPredictor:
    def __init__(self, folder=ROOT / "models"):
        self.folder = Path(folder)
        self.model, self.per_wilayah = self.load_model()

    def load_model(self):
        return _muat_semua(str(self.folder))

    def ambil(self, nama):
        """nama: 'gabungan', 'kabupaten', 'kota', atau kode kab/kota (model per wilayah)."""
        if nama in self.model:
            return self.model[nama]
        return self.per_wilayah.get(nama)

    def predict(self, rls, ahh_l, ahh_p, ppk_l, ppk_p, ikk, model="gabungan"):
        m = self.ambil(model)
        if m is None:
            return None
        nilai = [rls, ahh_l, ahh_p, ppk_l, ppk_p, ikk]
        X = pd.DataFrame([[np.nan if v is None else float(v) for v in nilai]], columns=FITUR)
        estimasi = float(m.predict(X)[0])
        sv = m.get_feature_importance(Pool(X), type="ShapValues")[0]
        return HasilEstimasi(estimasi=estimasi, nilai_dasar=float(sv[-1]),
                             shap=dict(zip(FITUR, map(float, sv[:-1]))))

    def shap_panel(self, df, model="gabungan"):
        """Kontribusi SHAP tiap fitur untuk setiap baris df (kolom shap_<fitur>)."""
        return _shap_panel(self.ambil(model), model, df[FITUR])

    def importance(self, model):
        """Feature importance global (PredictionValuesChange) satu model, dalam persen."""
        m = self.ambil(model)
        return dict(zip(FITUR, map(float, m.get_feature_importance())))
