"""Verifikasi: keluaran DataLoader (membaca data/kemiskinan.db) harus sama dengan CSV di hasil/
dan dengan keluaran DataLoader versi lama yang disimpan di /tmp/keluaran_lama/*.pkl.

Jalankan dari folder root proyek:
    python scripts/cek_database.py
Pembanding /tmp/keluaran_lama dilewati bila foldernya tidak ada.
"""

import logging
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

ROOT = Path(__file__).resolve().parent.parent
LAMA = Path("/tmp/keluaran_lama")
sys.path.insert(0, str(ROOT / "app"))
logging.disable(logging.WARNING)  # sembunyikan peringatan cache Streamlit di luar `streamlit run`

from data_loader import FITUR, DataLoader  # noqa: E402

gagal = []


def cek(nama, fungsi):
    try:
        fungsi()
        print(f"  LOLOS  {nama}")
    except AssertionError as e:
        gagal.append(nama)
        print(f"  GAGAL  {nama}\n{e}")


def csv(nama):
    return pd.read_csv(ROOT / "hasil" / nama, dtype={"kode_kabkota": str})


dl = DataLoader()
baru = {
    "load_hasil_estimasi": dl.load_hasil_estimasi(),
    "load_metrik": dl.load_metrik(),
    "load_metrik_per_kabkota": dl.load_metrik_per_kabkota(),
    "load_kontribusi": dl.load_kontribusi(),
    "daftar_wilayah": dl.daftar_wilayah(),
}

print("Dibandingkan dengan CSV di hasil/")
est = csv("hasil_estimasi.csv").sort_values(["kode_kabkota", "tahun"]).reset_index(drop=True)
cek("load_hasil_estimasi = hasil_estimasi.csv",
    lambda: assert_frame_equal(baru["load_hasil_estimasi"],
                               est[baru["load_hasil_estimasi"].columns.tolist()]))
cek("load_metrik = metrik_evaluasi.csv",
    lambda: assert_frame_equal(baru["load_metrik"], csv("metrik_evaluasi.csv")))
cek("load_metrik_per_kabkota = metrik_per_kabkota.csv",
    lambda: assert_frame_equal(baru["load_metrik_per_kabkota"], csv("metrik_per_kabkota.csv")))
cek("load_kontribusi = kontribusi_variabel.csv",
    lambda: assert_frame_equal(baru["load_kontribusi"], csv("kontribusi_variabel.csv")))


def kontribusi_lokal_presisi():
    a = baru["load_kontribusi"].query("model.str.startswith('per_kabkota')")
    b = csv("kontribusi_variabel.csv").query("model.str.startswith('per_kabkota')")
    selisih = max(np.abs(a[k].values - b[k].values).max()
                  for k in ("feature_importance", "mean_abs_shap"))
    print(f"         selisih maksimum rata-rata 119 model lokal: {selisih:.2e}")
    assert selisih < 1e-9, f"selisih {selisih} >= 1e-9"


cek("kontribusi rata-rata model lokal (< 1e-9)", kontribusi_lokal_presisi)

print(f"Dibandingkan dengan keluaran DataLoader lama ({LAMA})")
if not LAMA.exists():
    print("  dilewati: folder tidak ada")
else:
    for nama, df in baru.items():
        with open(LAMA / f"{nama}.pkl", "rb") as f:
            lama = pickle.load(f)
        cek(f"{nama} = versi lama", lambda: assert_frame_equal(df, lama))

    with open(LAMA / "rentang_latih_wilayah.pkl", "rb") as f:
        rentang_lama = pickle.load(f)

    def rentang_sama():
        for kode, isi in rentang_lama.items():
            r = dl.rentang_latih_wilayah(kode)
            for f in FITUR:
                np.testing.assert_allclose(r[f], isi[f], err_msg=f"{kode} {f}")

    cek(f"rentang_latih_wilayah = versi lama ({', '.join(rentang_lama)})", rentang_sama)

if gagal:
    sys.exit(f"\n{len(gagal)} pemeriksaan GAGAL: {gagal}")
print("\nSemua pemeriksaan lolos.")
