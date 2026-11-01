import json
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
FITUR = ["rls", "ahh_l", "ahh_p", "ppk_l", "ppk_p", "ikk"]

# Kolom estimasi yang dipakai dashboard dan nama model yang menghasilkannya
KOLOM_ESTIMASI = {
    "estimasi_kabkota": "Model per kab/kota",
    "estimasi_jenis": "Model kabupaten / kota",
    "estimasi_gabungan": "Model gabungan",
}

# Label baris tabel metrik (sama dengan hasil/metrik_evaluasi.csv) → (nama_model, cakupan)
LABEL_METRIK = {
    "Gabungan (119 kab/kota)": ("gabungan", "semua"),
    "Gabungan — subset kabupaten": ("gabungan", "kabupaten"),
    "Kabupaten (85)": ("kabupaten", "semua"),
    "Gabungan — subset kota": ("gabungan", "kota"),
    "Kota (34)": ("kota", "semua"),
}
LABEL_METRIK_LOKAL = "Per kab/kota (119 model, gabungan semua prediksi)"
LABEL_KONTRIBUSI_LOKAL = "per_kabkota (rata-rata 119 model)"

SQL_HASIL_ESTIMASI = """
SELECT d.kode_kabkota, k.nama_kabkota, d.tahun,
       d.rls, d.ahh_l, d.ahh_p, d.ppk_l, d.ppk_p, d.ikk,
       d.p0 AS p0_aktual,
       MAX(CASE WHEN m.tingkat_model = 'gabungan' THEN h.estimasi_p0 END) AS estimasi_gabungan,
       MAX(CASE WHEN m.tingkat_model = 'kelompok' THEN h.estimasi_p0 END) AS estimasi_jenis,
       MAX(CASE WHEN m.tingkat_model = 'lokal'    THEN h.estimasi_p0 END) AS estimasi_kabkota,
       p.nama_prov AS provinsi, k.jenis, d.jenis_data AS data
FROM data_indikator d
JOIN kabupaten_kota k ON k.kode_kabkota = d.kode_kabkota
JOIN provinsi p       ON p.kode_prov = k.kode_prov
JOIN hasil_estimasi h ON h.id_data = d.id_data
JOIN model m          ON m.id_model = h.id_model
GROUP BY d.id_data
ORDER BY d.kode_kabkota, d.tahun
"""

SQL_EVALUASI = """
SELECT m.nama_model, e.cakupan, e.rmse AS "RMSE", e.mae AS "MAE", e.mape AS "MAPE (%)",
       e.r2 AS "R2", e.jumlah_data AS n
FROM evaluasi_model e
JOIN model m ON m.id_model = e.id_model
WHERE m.tingkat_model IN ('gabungan', 'kelompok')
"""

# Prediksi model lokal pada data uji, untuk metrik gabungan 119 model
SQL_UJI_LOKAL = """
SELECT d.p0 AS aktual, h.estimasi_p0 AS prediksi
FROM hasil_estimasi h
JOIN model m          ON m.id_model = h.id_model
JOIN data_indikator d ON d.id_data = h.id_data
WHERE m.tingkat_model = 'lokal' AND d.jenis_data = 'uji'
"""

SQL_METRIK_PER_KABKOTA = """
SELECT k.kode_kabkota, k.nama_kabkota, k.jenis,
       m.jumlah_data_latih AS n_latih, e.jumlah_data AS n_uji,
       e.rmse AS "RMSE", e.mae AS "MAE", e.mape AS "MAPE (%)",
       (SELECT MIN(p0) FROM data_indikator d
         WHERE d.kode_kabkota = k.kode_kabkota AND d.jenis_data = 'latih') AS p0_latih_min,
       (SELECT MAX(p0) FROM data_indikator d
         WHERE d.kode_kabkota = k.kode_kabkota AND d.jenis_data = 'latih') AS p0_latih_max
FROM evaluasi_model e
JOIN model m          ON m.id_model = e.id_model
JOIN kabupaten_kota k ON k.kode_kabkota = m.kode_kabkota
WHERE m.tingkat_model = 'lokal' AND e.cakupan = 'wilayah'
"""

# P0 uji di luar rentang P0 latih wilayahnya
SQL_LUAR_RENTANG = """
SELECT u.kode_kabkota,
       MAX(u.p0 < r.lo OR u.p0 > r.hi) AS di_luar_rentang_latih
FROM data_indikator u
JOIN (SELECT kode_kabkota, MIN(p0) AS lo, MAX(p0) AS hi
        FROM data_indikator WHERE jenis_data = 'latih' GROUP BY kode_kabkota) r
  ON r.kode_kabkota = u.kode_kabkota
WHERE u.jenis_data = 'uji'
GROUP BY u.kode_kabkota
"""

SQL_KONTRIBUSI = """
SELECT m.nama_model AS model, kv.kode_variabel AS variabel,
       kv.feature_importance, kv.mean_abs_shap
FROM kontribusi_variabel kv
JOIN model m ON m.id_model = kv.id_model
WHERE m.tingkat_model IN ('gabungan', 'kelompok')
UNION ALL
SELECT ?, kv.kode_variabel, AVG(kv.feature_importance), AVG(kv.mean_abs_shap)
FROM kontribusi_variabel kv
JOIN model m ON m.id_model = kv.id_model
WHERE m.tingkat_model = 'lokal'
GROUP BY kv.kode_variabel
"""


def _kueri(path, sql, params=()):
    """Jalankan SELECT pada database dalam mode hanya-baca."""
    with sqlite3.connect(f"file:{Path(path).as_posix()}?mode=ro", uri=True) as con:
        return pd.read_sql(sql, con, params=params)


@st.cache_data(show_spinner=False)
def _baca_hasil_estimasi(path):
    return _kueri(path, SQL_HASIL_ESTIMASI)


@st.cache_data(show_spinner=False)
def _baca_metrik(path):
    eva = _kueri(path, SQL_EVALUASI).set_index(["nama_model", "cakupan"])
    baris = [{"model": label, **eva.loc[kunci].to_dict()} for label, kunci in LABEL_METRIK.items()]

    uji = _kueri(path, SQL_UJI_LOKAL)
    galat = uji["prediksi"] - uji["aktual"]
    baris.append({
        "model": LABEL_METRIK_LOKAL,
        "RMSE": float(np.sqrt((galat ** 2).mean())),
        "MAE": float(galat.abs().mean()),
        "MAPE (%)": float((galat.abs() / uji["aktual"]).mean() * 100),
        "R2": float(1 - (galat ** 2).sum() / ((uji["aktual"] - uji["aktual"].mean()) ** 2).sum()),
        "n": len(uji),
    })
    df = pd.DataFrame(baris)
    df["model"] = df["model"].astype("str")
    df["n"] = df["n"].astype("int64")
    return df


@st.cache_data(show_spinner=False)
def _baca_metrik_per_kabkota(path):
    df = _kueri(path, SQL_METRIK_PER_KABKOTA)
    luar = _kueri(path, SQL_LUAR_RENTANG)
    df = df.merge(luar, on="kode_kabkota", how="left")
    df["di_luar_rentang_latih"] = df["di_luar_rentang_latih"].astype(bool)
    return df.sort_values("RMSE", kind="stable").reset_index(drop=True)


@st.cache_data(show_spinner=False)
def _baca_kontribusi(path, label_fitur):
    df = _kueri(path, SQL_KONTRIBUSI, params=(LABEL_KONTRIBUSI_LOKAL,))
    urutan_model = {"gabungan": 0, "kabupaten": 1, "kota": 2, LABEL_KONTRIBUSI_LOKAL: 3}
    df = df.sort_values(["model", "variabel"], key=lambda s: s.map(
        urutan_model if s.name == "model" else {f: i for i, f in enumerate(FITUR)}))
    df["label"] = df["variabel"].map(dict(label_fitur)).astype("str")
    return df.reset_index(drop=True)


@st.cache_data(show_spinner=False)
def _baca_variabel(path):
    return _kueri(path, "SELECT * FROM variabel ORDER BY rowid")


@st.cache_data(show_spinner=False)
def _baca_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class DataLoader:
    def __init__(self, root=ROOT):
        self.root = Path(root)
        self.db = str(self.root / "data" / "kemiskinan.db")

    def load_hasil_estimasi(self):
        """Panel kab/kota × tahun: 6 fitur, P0 aktual, estimasi ketiga tingkat model, wilayah."""
        return _baca_hasil_estimasi(self.db)

    def filter_wilayah(self, df, provinsi=None, jenis=None, kode_kabkota=None, tahun=None):
        """Saring tabel berdasarkan provinsi, jenis, kode wilayah, dan rentang tahun (awal, akhir)."""
        if provinsi:
            df = df[df["provinsi"] == provinsi]
        if jenis:
            df = df[df["jenis"] == jenis]
        if kode_kabkota:
            df = df[df["kode_kabkota"] == kode_kabkota]
        if tahun:
            df = df[df["tahun"].between(tahun[0], tahun[1])]
        return df

    def load_metadata(self):
        return _baca_json(self.root / "models" / "metadata.json")

    def load_metrik(self):
        """Metrik data uji per model; baris model lokal dihitung dari hasil_estimasi."""
        return _baca_metrik(self.db)

    def load_metrik_per_kabkota(self):
        """Metrik data uji tiap model lokal, urut RMSE naik."""
        return _baca_metrik_per_kabkota(self.db)

    def load_kontribusi(self):
        """Kontribusi variabel model gabungan, kabupaten, kota, dan rata-rata 119 model lokal."""
        label = tuple(self.load_metadata()["label_fitur"].items())
        return _baca_kontribusi(self.db, label)

    def load_variabel(self):
        """Isi tabel variabel: kode, nama, satuan, sumber publikasi BPS, dan peran."""
        return _baca_variabel(self.db)

    def daftar_wilayah(self):
        """Satu baris per kab/kota: kode, nama, provinsi, jenis (urut kode BPS)."""
        df = self.load_hasil_estimasi()
        return (df[["kode_kabkota", "nama_kabkota", "provinsi", "jenis"]]
                .drop_duplicates("kode_kabkota").sort_values("kode_kabkota")
                .reset_index(drop=True))

    def rentang_latih_wilayah(self, kode_kabkota):
        """Min–maks tiap fitur pada baris latih satu kab/kota (rentang model per wilayah)."""
        df = self.load_hasil_estimasi()
        latih = df[(df["kode_kabkota"] == kode_kabkota) & (df["data"] == "latih")]
        return {f: (latih[f].min(), latih[f].max()) for f in FITUR}
