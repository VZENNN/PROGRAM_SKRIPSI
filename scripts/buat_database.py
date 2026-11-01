"""Membentuk basis data SQLite data/kemiskinan.db (8 tabel, sesuai ERD Bab 3) dari hasil pelatihan.

Sumber : hasil/hasil_estimasi.csv, hasil/metrik_evaluasi.csv, hasil/metrik_per_kabkota.csv,
         hasil/kontribusi_variabel.csv, models/metadata.json, dan file .pkl di models/
Tujuan : data/kemiskinan.db

Jalankan dari folder root proyek setiap kali hasil Colab diperbarui:
    python scripts/buat_database.py
Dashboard hanya membaca database ini, tidak pernah menulis ke dalamnya.
"""

import json
import pickle
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import Pool

ROOT = Path(__file__).resolve().parent.parent
HASIL = ROOT / "hasil"
MODELS = ROOT / "models"
TUJUAN = ROOT / "data" / "kemiskinan.db"

FITUR = ["rls", "ahh_l", "ahh_p", "ppk_l", "ppk_p", "ikk"]

SKEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE provinsi (
    kode_prov TEXT PRIMARY KEY,
    nama_prov TEXT NOT NULL
);
CREATE TABLE kabupaten_kota (
    kode_kabkota TEXT PRIMARY KEY,
    kode_prov    TEXT NOT NULL REFERENCES provinsi(kode_prov),
    nama_kabkota TEXT NOT NULL,
    jenis        TEXT NOT NULL CHECK (jenis IN ('Kabupaten', 'Kota'))
);
CREATE TABLE variabel (
    kode_variabel TEXT PRIMARY KEY,
    nama_variabel TEXT NOT NULL,
    satuan        TEXT NOT NULL,
    sumber        TEXT NOT NULL,
    peran         TEXT NOT NULL CHECK (peran IN ('prediktor', 'target'))
);
CREATE TABLE data_indikator (
    id_data      INTEGER PRIMARY KEY,
    kode_kabkota TEXT    NOT NULL REFERENCES kabupaten_kota(kode_kabkota),
    tahun        INTEGER NOT NULL,
    rls REAL, ahh_l REAL, ahh_p REAL, ppk_l REAL, ppk_p REAL, ikk REAL,
    p0           REAL    NOT NULL,
    jenis_data   TEXT    NOT NULL CHECK (jenis_data IN ('latih', 'uji')),
    UNIQUE (kode_kabkota, tahun)
);
CREATE TABLE model (
    id_model          INTEGER PRIMARY KEY,
    nama_model        TEXT    NOT NULL UNIQUE,
    tingkat_model     TEXT    NOT NULL CHECK (tingkat_model IN ('gabungan', 'kelompok', 'lokal')),
    kode_kabkota      TEXT    REFERENCES kabupaten_kota(kode_kabkota),
    nama_file         TEXT    NOT NULL,
    iterations        INTEGER NOT NULL,
    depth             INTEGER NOT NULL,
    learning_rate     REAL    NOT NULL,
    l2_leaf_reg       REAL    NOT NULL,
    random_strength   REAL    NOT NULL,
    jumlah_data_latih INTEGER NOT NULL
);
CREATE TABLE hasil_estimasi (
    id_estimasi INTEGER PRIMARY KEY,
    id_data     INTEGER NOT NULL REFERENCES data_indikator(id_data),
    id_model    INTEGER NOT NULL REFERENCES model(id_model),
    estimasi_p0 REAL    NOT NULL,
    UNIQUE (id_data, id_model)
);
CREATE TABLE evaluasi_model (
    id_evaluasi INTEGER PRIMARY KEY,
    id_model    INTEGER NOT NULL REFERENCES model(id_model),
    cakupan     TEXT    NOT NULL,
    rmse REAL NOT NULL, mae REAL NOT NULL, mape REAL NOT NULL, r2 REAL,
    jumlah_data INTEGER NOT NULL,
    UNIQUE (id_model, cakupan)
);
CREATE TABLE kontribusi_variabel (
    id_kontribusi      INTEGER PRIMARY KEY,
    id_model           INTEGER NOT NULL REFERENCES model(id_model),
    kode_variabel      TEXT    NOT NULL REFERENCES variabel(kode_variabel),
    feature_importance REAL    NOT NULL,
    mean_abs_shap      REAL    NOT NULL,
    UNIQUE (id_model, kode_variabel)
);
"""

# Dua digit awal kode BPS menunjukkan provinsi
PROVINSI = {
    "31": "DKI Jakarta", "32": "Jawa Barat", "33": "Jawa Tengah",
    "34": "DI Yogyakarta", "35": "Jawa Timur", "36": "Banten",
}

VARIABEL = [
    ("rls", "Rata-rata Lama Sekolah", "tahun",
     "[Metode Baru] Rata-rata Lama Sekolah", "prediktor"),
    ("ahh_l", "Angka Harapan Hidup Laki-laki", "tahun",
     "Angka Harapan Hidup (AHH) Menurut Kabupaten/Kota dan Jenis Kelamin", "prediktor"),
    ("ahh_p", "Angka Harapan Hidup Perempuan", "tahun",
     "Angka Harapan Hidup (AHH) Menurut Kabupaten/Kota dan Jenis Kelamin", "prediktor"),
    ("ppk_l", "Pengeluaran per Kapita Laki-laki", "ribu rupiah/orang/tahun",
     "Pengeluaran per Kapita yang Disesuaikan menurut Jenis Kelamin", "prediktor"),
    ("ppk_p", "Pengeluaran per Kapita Perempuan", "ribu rupiah/orang/tahun",
     "Pengeluaran per Kapita yang Disesuaikan menurut Jenis Kelamin", "prediktor"),
    ("ikk", "Indeks Kemahalan Konstruksi", "indeks",
     "Indeks Kemahalan Konstruksi Kabupaten/Kota", "prediktor"),
    ("p0", "Persentase Penduduk Miskin", "persen",
     "Persentase Penduduk Miskin (P0) Menurut Kabupaten/Kota", "target"),
]

# Label baris metrik_evaluasi.csv → (nama_model, cakupan) di tabel evaluasi_model.
# Baris "Per kab/kota (119 model, ...)" tidak disimpan; dashboard menghitungnya dari hasil_estimasi.
LABEL_EVALUASI = {
    "Gabungan (119 kab/kota)": ("gabungan", "semua"),
    "Gabungan — subset kabupaten": ("gabungan", "kabupaten"),
    "Kabupaten (85)": ("kabupaten", "semua"),
    "Gabungan — subset kota": ("gabungan", "kota"),
    "Kota (34)": ("kota", "semua"),
}

JUMLAH_BARIS = {
    "provinsi": 6, "kabupaten_kota": 119, "variabel": 7, "data_indikator": 1308,
    "model": 122, "hasil_estimasi": 3924, "evaluasi_model": 124, "kontribusi_variabel": 732,
}


def kosong_ke_null(v):
    return None if pd.isna(v) else float(v)


def muat_pickle(path):
    with open(path, "rb") as f:
        return pickle.load(f)


def main():
    meta = json.loads((MODELS / "metadata.json").read_text(encoding="utf-8"))
    hp = meta["hiperparameter"]
    est = pd.read_csv(HASIL / "hasil_estimasi.csv", dtype={"kode_kabkota": str})
    met = pd.read_csv(HASIL / "metrik_evaluasi.csv")
    mk = pd.read_csv(HASIL / "metrik_per_kabkota.csv", dtype={"kode_kabkota": str})
    kon = pd.read_csv(HASIL / "kontribusi_variabel.csv")
    lokal = muat_pickle(MODELS / "model_per_kabkota.pkl")  # dict {kode_kabkota: CatBoostRegressor}

    est = est.sort_values(["kode_kabkota", "tahun"]).reset_index(drop=True)
    est["id_data"] = np.arange(1, len(est) + 1)
    latih = est[est["data"] == "latih"]
    uji = est[est["data"] == "uji"]

    TUJUAN.parent.mkdir(parents=True, exist_ok=True)
    TUJUAN.unlink(missing_ok=True)  # dibuat ulang dari nol agar selalu sama dengan sumber
    con = sqlite3.connect(TUJUAN)
    con.executescript(SKEMA)

    # provinsi & kabupaten_kota
    con.executemany("INSERT INTO provinsi VALUES (?, ?)", sorted(PROVINSI.items()))
    wil = est.drop_duplicates("kode_kabkota")
    con.executemany(
        "INSERT INTO kabupaten_kota VALUES (?, ?, ?, ?)",
        [(r.kode_kabkota, r.kode_kabkota[:2], r.nama_kabkota, r.jenis) for r in wil.itertuples()])

    # variabel
    con.executemany("INSERT INTO variabel VALUES (?, ?, ?, ?, ?)", VARIABEL)

    # data_indikator: satu baris per kab/kota × tahun; IKK kosong disimpan sebagai NULL
    con.executemany(
        "INSERT INTO data_indikator VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [(int(r.id_data), r.kode_kabkota, int(r.tahun),
          *[kosong_ke_null(getattr(r, f)) for f in FITUR], float(r.p0_aktual), r.data)
         for r in est.itertuples()])

    # model: 1 gabungan, 2 kelompok (kabupaten, kota), 119 lokal (per kab/kota)
    baris_model, id_model = [], {}

    def tambah_model(nama, tingkat, kode, nama_file, param, n_latih):
        id_model[nama] = len(baris_model) + 1
        baris_model.append((
            id_model[nama], nama, tingkat, kode, nama_file,
            int(param["iterations"]), int(param["depth"]), float(param["learning_rate"]),
            float(param["l2_leaf_reg"]),
            float(param.get("random_strength", 1.0)),  # model lokal memakai bawaan CatBoost (1)
            int(n_latih)))

    tambah_model("gabungan", "gabungan", None, "models/model_gabungan.pkl",
                 hp["gabungan"], len(latih))
    tambah_model("kabupaten", "kelompok", None, "models/model_kabupaten.pkl",
                 hp["kabupaten"], (latih["jenis"] == "Kabupaten").sum())
    tambah_model("kota", "kelompok", None, "models/model_kota.pkl",
                 hp["kota"], (latih["jenis"] == "Kota").sum())
    for kode in sorted(lokal):
        tambah_model(f"lokal_{kode}", "lokal", kode, "models/model_per_kabkota.pkl",
                     hp["per_kabkota"], (latih["kode_kabkota"] == kode).sum())
    con.executemany("INSERT INTO model VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", baris_model)

    # hasil_estimasi: tiga baris per data (gabungan, kelompok sesuai jenis, lokal wilayahnya)
    baris_estimasi = []
    for r in est.itertuples():
        kelompok = "kabupaten" if r.jenis == "Kabupaten" else "kota"
        baris_estimasi += [
            (int(r.id_data), id_model["gabungan"], float(r.estimasi_gabungan)),
            (int(r.id_data), id_model[kelompok], float(r.estimasi_jenis)),
            (int(r.id_data), id_model[f"lokal_{r.kode_kabkota}"], float(r.estimasi_kabkota)),
        ]
    con.executemany(
        "INSERT INTO hasil_estimasi (id_data, id_model, estimasi_p0) VALUES (?, ?, ?)",
        baris_estimasi)

    # evaluasi_model
    baris_evaluasi = [
        (id_model[LABEL_EVALUASI[r["model"]][0]], LABEL_EVALUASI[r["model"]][1],
         r["RMSE"], r["MAE"], r["MAPE (%)"], r["R2"], int(r["n"]))
        for _, r in met.iterrows() if r["model"] in LABEL_EVALUASI]
    baris_evaluasi += [
        (id_model[f"lokal_{r['kode_kabkota']}"], "wilayah",
         r["RMSE"], r["MAE"], r["MAPE (%)"], None, int(r["n_uji"]))
        for _, r in mk.iterrows()]
    con.executemany(
        "INSERT INTO evaluasi_model (id_model, cakupan, rmse, mae, mape, r2, jumlah_data) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)", baris_evaluasi)

    # kontribusi_variabel: model gabungan & kelompok dari CSV, 119 model lokal dihitung per model
    baris_kontribusi = [
        (id_model[nama], r["variabel"], r["feature_importance"], r["mean_abs_shap"])
        for nama in ("gabungan", "kabupaten", "kota")
        for _, r in kon[kon["model"] == nama].iterrows()]
    for kode, m in sorted(lokal.items()):
        te = uji[uji["kode_kabkota"] == kode]
        fi = m.get_feature_importance(type="PredictionValuesChange")
        sv = m.get_feature_importance(Pool(te[FITUR]), type="ShapValues")
        for f, a, b in zip(FITUR, fi, np.abs(sv[:, :-1]).mean(axis=0)):
            baris_kontribusi.append((id_model[f"lokal_{kode}"], f, float(a), float(b)))
    con.executemany(
        "INSERT INTO kontribusi_variabel (id_model, kode_variabel, feature_importance, mean_abs_shap) "
        "VALUES (?, ?, ?, ?)", baris_kontribusi)

    con.commit()

    # Pemeriksaan akhir
    salah = []
    print(f"{TUJUAN.relative_to(ROOT)}")
    for tabel, harus in JUMLAH_BARIS.items():
        n = con.execute(f"SELECT COUNT(*) FROM {tabel}").fetchone()[0]
        print(f"  {tabel:<20} {n:>5}" + ("" if n == harus else f"  (seharusnya {harus})"))
        if n != harus:
            salah.append(tabel)
    fk = con.execute("PRAGMA foreign_key_check").fetchall()
    print(f"  foreign_key_check    {fk if fk else 'kosong (tidak ada pelanggaran)'}")
    con.close()

    if salah or fk:
        sys.exit(f"Gagal: jumlah baris tidak sesuai {salah} atau ada pelanggaran foreign key {fk}")


if __name__ == "__main__":
    main()
