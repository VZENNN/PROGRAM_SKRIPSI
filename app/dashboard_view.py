import html

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from data_loader import FITUR, KOLOM_ESTIMASI
from slider_beranda import logo_sdg1, tampilkan_slider
from tema import (AKSEN, AKTUAL, BATA, GARIS, OKER, REDUP, WARNA_PROVINSI,
                  angka, catatan, deret_angka, grafik, kepala)

SATUAN = {"rls": "tahun", "ahh_l": "tahun", "ahh_p": "tahun",
          "ppk_l": "ribu Rp/tahun", "ppk_p": "ribu Rp/tahun", "ikk": "indeks"}
LANGKAH_INPUT = {"rls": 0.01, "ahh_l": 0.01, "ahh_p": 0.01,
                 "ppk_l": 10.0, "ppk_p": 10.0, "ikk": 0.1}
HALAMAN = [
    ("Beranda", ":material/home:"),
    ("Estimasi", ":material/calculate:"),
    ("Kontribusi Variabel", ":material/bar_chart:"),
    ("Informasi", ":material/info:"),
]
NAMA_MODEL_KONTRIBUSI = {
    "gabungan": "Gabungan",
    "kabupaten": "Kabupaten",
    "kota": "Kota",
    "per_kabkota (rata-rata 119 model)": "Per kab/kota (rata-rata 119 model)",
}


def _tabel_html(header, baris, kolom_angka=()):
    """Tabel HTML sederhana; kolom_angka = indeks kolom yang rata kanan."""
    th = "".join(f'<th class="{"angka" if i in kolom_angka else ""}">{h}</th>'
                 for i, h in enumerate(header))
    tr = "".join(
        "<tr>" + "".join(f'<td class="{"angka" if i in kolom_angka else ""}">{v}</td>'
                         for i, v in enumerate(b)) + "</tr>"
        for b in baris)
    return f'<table class="tabel-info"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table>'


class DashboardView:
    def __init__(self, loader, predictor_fn):
        self.loader = loader
        self._predictor_fn = predictor_fn 
        self.meta = loader.load_metadata()
        self.label = self.meta["label_fitur"]

    @property
    def predictor(self):
        return self._predictor_fn()

    def _urutan_provinsi(self, df):
        return list(df.sort_values("kode_kabkota")["provinsi"].drop_duplicates())

    # ------------------------------------------------------------------ Sidebar
    def tampilkan_sidebar(self):
        """Gambar sidebar dan kembalikan nama halaman yang sedang aktif."""
        if "halaman" not in st.session_state:
            st.session_state["halaman"] = HALAMAN[0][0]

        def pindah(nama):
            st.session_state["halaman"] = nama

        df = self.loader.load_hasil_estimasi()
        met = self.loader.load_metrik()
        terbaik = met.loc[met["RMSE"].idxmin()]
        n_model = 3 + len(self.loader.load_metrik_per_kabkota())

        with st.sidebar:
            st.markdown(
                f'<div class="merek"><img src="{logo_sdg1()}" alt="SDG 1">'
                '<div><div class="kode">Skripsi · Teknik Informatika</div>'
                '<div class="nama">Persentase Penduduk Miskin Pulau Jawa</div></div></div>'
                '<div class="judul-sb">Menu</div>',
                unsafe_allow_html=True)
            for nama, ikon in HALAMAN:
                aktif = st.session_state["halaman"] == nama
                st.button(nama, icon=ikon, key=f"nav_{nama}", width="stretch",
                          type="primary" if aktif else "secondary",
                          on_click=pindah, args=(nama,))

            st.markdown(
                '<div class="judul-sb">Ringkasan data</div><div class="ringkas-sb">'
                f'<div><b>{df.kode_kabkota.nunique()}</b><span>kabupaten/kota</span></div>'
                f'<div><b>{df.tahun.nunique()}</b><span>tahun ({df.tahun.min()}–{df.tahun.max()})</span></div>'
                f'<div><b>{len(FITUR)}</b><span>variabel prediktor</span></div>'
                f'<div><b>{n_model}</b><span>model CatBoost</span></div></div>'
                '<div class="judul-sb">RMSE terendah · data uji</div>'
                f'<div class="terbaik-sb"><div class="nm">{html.escape(terbaik["model"])}</div>'
                f'<div class="ang"><div><span>RMSE</span> {angka(terbaik["RMSE"], 3)}</div>'
                f'<div><span>R²</span> {angka(terbaik["R2"], 3)}</div>'
                f'<div><span>MAPE</span> {angka(terbaik["MAPE (%)"], 1)}%</div></div></div>'
                '<div class="kaki-sidebar">Sumber data: Badan Pusat Statistik<br>'
                'Metode: CatBoost Regression<br>Fakultas Teknologi Informasi Universitas Tarumanagara</div>',
                unsafe_allow_html=True)
        return st.session_state["halaman"]

    # ------------------------------------------------------------------ Beranda
    def tampilkan_beranda(self):
        df = self.loader.load_hasil_estimasi()
        th0, th1 = int(df.tahun.min()), int(df.tahun.max())
        wil = self.loader.daftar_wilayah()
        n_kab = int((wil.jenis == "Kabupaten").sum())
        n_kota = int((wil.jenis == "Kota").sum())
        n_model = 3 + len(self.loader.load_metrik_per_kabkota())
        rata = df.groupby("tahun")["p0_aktual"].mean()

        kepala(
            "Skripsi · CatBoost Regression",
            "Persentase Penduduk Miskin Kabupaten/Kota di Pulau Jawa",
            "Dashboard ini menyajikan hasil pemodelan persentase penduduk miskin (P0) "
            "dari enam indikator pendidikan, kesehatan, pengeluaran, dan kemahalan "
            f"konstruksi, berdasarkan publikasi resmi BPS tahun {th0}–{th1}.",
        )
        tampilkan_slider()
        deret_angka([
            ("Kabupaten/kota", len(wil), "", f"{n_kab} kabupaten · {n_kota} kota"),
            ("Periode data", f"{th0}–{th1}", "", f"{angka(len(df), 0)} observasi panel"),
            (f"Rata-rata P0 {th1}", angka(rata[th1]), "%",
             f"{th0}: {angka(rata[th0])}% · rata-rata sederhana antarwilayah"),
            ("Model dilatih", n_model, "", "1 gabungan · 2 per jenis · per kab/kota"),
        ])

        st.markdown("## Perkembangan P0 per provinsi")
        per_prov = df.groupby(["provinsi", "tahun"])["p0_aktual"].mean().reset_index()
        fig = go.Figure()
        for prov in self._urutan_provinsi(df):
            d = per_prov[per_prov.provinsi == prov]
            fig.add_scatter(x=d.tahun, y=d.p0_aktual, name=prov, mode="lines+markers",
                            line=dict(width=2, color=WARNA_PROVINSI.get(prov)),
                            marker=dict(size=5),
                            hovertemplate=f"{prov}<br>%{{x}}: %{{y:.2f}}%<extra></extra>")
        fig.update_layout(yaxis_title="P0 (%)", xaxis=dict(dtick=1))
        grafik(fig, 360)
        catatan("Garis menunjukkan rata-rata sederhana P0 kabupaten/kota di tiap provinsi, "
                "bukan angka kemiskinan provinsi resmi BPS (yang ditimbang jumlah penduduk).")

        kiri, kanan = st.columns([1.25, 1], gap="large")
        with kiri:
            st.markdown("## Cara memakai dashboard")
            st.markdown("""
<ol class="langkah">
<li><b>Estimasi hasil pra-hitung</b><span>Pilih provinsi, jenis wilayah, rentang tahun, dan model
untuk melihat P0 aktual BPS berdampingan dengan hasil estimasi model.</span></li>
<li><b>Estimasi simulasi</b><span>Pilih kabupaten/kota, ubah nilai enam indikator, lalu tekan
<i>Estimasi</i> untuk mendapat perkiraan P0 dan kontribusi tiap variabel.</span></li>
<li><b>Kontribusi Variabel</b><span>Lihat variabel mana yang paling berpengaruh pada masing-masing
model, serta arah pengaruhnya.</span></li>
<li><b>Informasi</b><span>Cara kerja, metode, sumber data, dan hasil evaluasi model.</span></li>
</ol>""", unsafe_allow_html=True)
        with kanan:
            st.markdown(f"## P0 tahun {th1}")
            akhir = df[df.tahun == th1].sort_values("p0_aktual", ascending=False)
            for judul, bag in (("Tertinggi", akhir.head(5)), ("Terendah", akhir.tail(5)[::-1])):
                st.markdown(f"**{judul}**")
                st.markdown(_tabel_html(
                    ["Kabupaten/kota", "Provinsi", "P0 (%)"],
                    [[html.escape(r.nama_kabkota), r.provinsi, angka(r.p0_aktual)]
                     for r in bag.itertuples()],
                    kolom_angka=(2,)), unsafe_allow_html=True)

    # ----------------------------------------------------------------- Estimasi
    def tampilkan_estimasi(self):
        kepala("Modul 2", "Estimasi P0",
               "Bandingkan P0 aktual dengan hasil estimasi model, atau simulasikan "
               "nilai indikator sendiri untuk satu kabupaten/kota.")
        tab_statis, tab_rt = st.tabs(["Hasil pra-hitung", "Simulasi real-time"])
        with tab_statis:
            self.tampilkan_statis()
        with tab_rt:
            self.tampilkan_form_input()

    def tampilkan_statis(self):
        df = self.loader.load_hasil_estimasi()
        th0, th1 = int(df.tahun.min()), int(df.tahun.max())

        c1, c2, c3, c4 = st.columns([1.2, 0.9, 1.4, 1.3])
        provinsi = c1.selectbox("Provinsi", ["Semua provinsi"] + self._urutan_provinsi(df),
                                key="st_prov")
        jenis = c2.selectbox("Jenis wilayah", ["Semua", "Kabupaten", "Kota"], key="st_jenis")
        tahun = c3.slider("Rentang tahun", th0, th1, (th0, th1), key="st_tahun")
        kol = c4.selectbox("Model estimasi", list(KOLOM_ESTIMASI), format_func=KOLOM_ESTIMASI.get,
                           key="st_model")

        sub = self.loader.filter_wilayah(
            df,
            provinsi=None if provinsi == "Semua provinsi" else provinsi,
            jenis=None if jenis == "Semua" else jenis,
            tahun=tahun,
        )
        if sub.empty:
            st.info("Tidak ada data untuk kombinasi filter ini.")
            return

        uji = sub[sub.data == "uji"].dropna(subset=[kol, "p0_aktual"])
        if len(uji):
            galat = uji[kol] - uji.p0_aktual
            rmse = angka(float(np.sqrt((galat ** 2).mean())))
            mae = angka(float(galat.abs().mean()))
            mape = angka(float((galat.abs() / uji.p0_aktual).mean() * 100))
            ket_uji = f"{len(uji)} baris uji"
        else:
            rmse = mae = mape = "–"
            ket_uji = "filter tidak mencakup 2023–2024"
        deret_angka([
            ("Baris ditampilkan", angka(len(sub), 0), "", f"{sub.kode_kabkota.nunique()} kab/kota"),
            ("RMSE data uji", rmse, "", ket_uji),
            ("MAE data uji", mae, "", "poin persen P0"),
            ("MAPE data uji", mape, "%" if len(uji) else "", KOLOM_ESTIMASI[kol].lower()),
        ])

        kiri, kanan = st.columns([1.35, 1], gap="large")
        with kiri:
            wil = sub.drop_duplicates("kode_kabkota").sort_values("kode_kabkota")
            nama = dict(zip(wil.kode_kabkota, wil.nama_kabkota))
            kode = st.selectbox("Kabupaten/kota", list(nama), format_func=nama.get)
            d = sub[sub.kode_kabkota == kode].sort_values("tahun")
            fig = go.Figure()
            if d.tahun.max() >= 2023:
                fig.add_vrect(x0=max(2022.5, d.tahun.min() - 0.5), x1=d.tahun.max() + 0.5,
                              fillcolor=OKER, opacity=0.09, line_width=0,
                              annotation_text="periode uji", annotation_position="top left",
                              annotation_font=dict(size=11, color=OKER))
            fig.add_scatter(x=d.tahun, y=d.p0_aktual, name="P0 aktual BPS", mode="lines+markers",
                            line=dict(color=AKTUAL, width=2), marker=dict(size=6),
                            hovertemplate="%{x}: %{y:.2f}%<extra>aktual</extra>")
            fig.add_scatter(x=d.tahun, y=d[kol], name=KOLOM_ESTIMASI[kol], mode="lines+markers",
                            line=dict(color=AKSEN, width=2, dash="dot"),
                            marker=dict(size=6, symbol="diamond"),
                            hovertemplate="%{x}: %{y:.2f}%<extra>estimasi</extra>")
            fig.update_layout(yaxis_title="P0 (%)", xaxis=dict(dtick=1),
                              title=dict(text=nama[kode], font=dict(size=14), x=0, xref="paper", y=0.98))
            grafik(fig, 380)

        with kanan:
            st.markdown("<div style='height:4.1rem'></div>", unsafe_allow_html=True)
            fig = go.Figure()
            for bag, warna, label in (("latih", "#9DB7B5", "Data latih"), ("uji", OKER, "Data uji")):
                b = sub[sub.data == bag]
                fig.add_scatter(x=b.p0_aktual, y=b[kol], mode="markers", name=label,
                                marker=dict(color=warna, size=6, opacity=0.8,
                                            line=dict(width=0.5, color="#FFFFFF")),
                                text=b.nama_kabkota + " " + b.tahun.astype(str),
                                hovertemplate="%{text}<br>aktual %{x:.2f}% · estimasi %{y:.2f}%<extra></extra>")
            batas = [0, float(np.nanmax(sub[["p0_aktual", kol]].values)) * 1.05]
            fig.add_scatter(x=batas, y=batas, mode="lines", showlegend=False, hoverinfo="skip",
                            line=dict(color=REDUP, width=1, dash="dash"))
            fig.update_layout(xaxis_title="P0 aktual (%)", yaxis_title="P0 estimasi (%)",
                              title=dict(text="Aktual vs estimasi", font=dict(size=14), x=0, xref="paper", y=0.98))
            grafik(fig, 380)

        st.markdown("### Tabel hasil estimasi")
        tabel = sub[["kode_kabkota", "nama_kabkota", "provinsi", "tahun", "data", "p0_aktual", kol]].copy()
        tabel["selisih"] = tabel[kol] - tabel["p0_aktual"]
        tabel = tabel.sort_values(["tahun", "kode_kabkota"], ascending=[False, True])
        st.dataframe(
            tabel, hide_index=True, height=360,
            column_config={
                "kode_kabkota": "Kode",
                "nama_kabkota": "Kabupaten/kota",
                "provinsi": "Provinsi",
                "tahun": st.column_config.NumberColumn("Tahun", format="%d"),
                "data": "Data",
                "p0_aktual": st.column_config.NumberColumn("P0 aktual (%)", format="%.2f"),
                kol: st.column_config.NumberColumn("Estimasi (%)", format="%.2f"),
                "selisih": st.column_config.NumberColumn("Selisih", format="%+.2f"),
            },
        )
        st.download_button("Unduh tabel (CSV)", tabel.to_csv(index=False).encode("utf-8"),
                           file_name="hasil_estimasi_terfilter.csv", mime="text/csv")

    def tampilkan_form_input(self):
        df = self.loader.load_hasil_estimasi()
        wil = self.loader.daftar_wilayah()
        info = {r.kode_kabkota: r for r in wil.itertuples()}
        rentang = self.meta["rentang_fitur_latih"]

        c1, c2 = st.columns([2, 1])
        kode = c1.selectbox("Kabupaten/kota", list(info), key="rt_kode",
                            format_func=lambda k: f"{info[k].nama_kabkota} · {info[k].provinsi}")
        tahun_list = sorted(df.tahun.unique(), reverse=True)
        tahun_acuan = c2.selectbox("Isi awal dari data tahun", tahun_list, key="rt_tahun")
        acuan = df[(df.kode_kabkota == kode) & (df.tahun == tahun_acuan)].iloc[0]

        catatan("Nilai awal diambil dari data BPS wilayah dan tahun yang dipilih. "
                "Ubah satu atau beberapa nilai untuk melihat bagaimana estimasi P0 berubah.")

        with st.form("form_estimasi"):
            kolom = st.columns(3)
            nilai = {}
            for i, f in enumerate(FITUR):
                awal = acuan[f]
                r = rentang[f]
                nilai[f] = kolom[i % 3].number_input(
                    f"{self.label[f]} ({SATUAN[f]})",
                    value=None if awal != awal else float(awal),
                    step=LANGKAH_INPUT[f], format="%.2f",
                    key=f"in_{f}_{kode}_{tahun_acuan}",
                    help=f"Rentang data latih: {angka(r['min'])} – {angka(r['max'])}",
                )
            kirim = st.form_submit_button("Estimasi")

        if kirim:
            st.session_state["hasil_rt"] = {"kode": kode, "tahun": tahun_acuan, "nilai": nilai}
        h = st.session_state.get("hasil_rt")
        if not h or h["kode"] != kode or h["tahun"] != tahun_acuan:
            return
        nilai = h["nilai"]

        # Peringatan input di luar rentang data latih
        kosong = [self.label[f] for f in FITUR if nilai[f] is None]
        luar_global = [f for f in FITUR if nilai[f] is not None
                       and not rentang[f]["min"] <= nilai[f] <= rentang[f]["max"]]
        r_wil = self.loader.rentang_latih_wilayah(kode)
        luar_wil = [f for f in FITUR if nilai[f] is not None and r_wil[f][0] == r_wil[f][0]
                    and not r_wil[f][0] <= nilai[f] <= r_wil[f][1]]
        pesan = []
        if kosong:
            pesan.append("Nilai kosong (ditangani sebagai <i>missing</i> oleh CatBoost): "
                         + ", ".join(kosong))
        for f in luar_global:
            pesan.append(f"{self.label[f]} = {angka(nilai[f])} di luar rentang data latih "
                         f"seluruh wilayah ({angka(rentang[f]['min'])} – {angka(rentang[f]['max'])}).")
        if luar_wil:
            pesan.append("Di luar rentang data latih 2014–2022 wilayah ini. Model per kab/kota "
                         "memperlakukan nilai tersebut seperti nilai terdekat yang pernah "
                         "dipelajari: " + ", ".join(
                             f"{self.label[f]} ({angka(r_wil[f][0])} – {angka(r_wil[f][1])})"
                             for f in luar_wil))
        if pesan:
            st.markdown('<div class="peringatan"><b>Perhatian</b><ul>'
                        + "".join(f"<li>{p}</li>" for p in pesan) + "</ul></div>",
                        unsafe_allow_html=True)

        p = self.predictor
        model_jenis = "kabupaten" if info[kode].jenis == "Kabupaten" else "kota"
        hasil = {
            "wilayah": p.predict(**nilai, model=kode),
            model_jenis: p.predict(**nilai, model=model_jenis),
            "gabungan": p.predict(**nilai, model="gabungan"),
        }
        nama_model = {"wilayah": f"Model per kab/kota ({info[kode].nama_kabkota})",
                      model_jenis: f"Model {model_jenis}", "gabungan": "Model gabungan"}
        utama = "wilayah" if hasil["wilayah"] else model_jenis
        diubah = any(
            (nilai[f] is None) != (acuan[f] != acuan[f])
            or (nilai[f] is not None and acuan[f] == acuan[f] and abs(nilai[f] - acuan[f]) > 1e-9)
            for f in FITUR)

        kiri, kanan = st.columns([1, 1.5], gap="large")
        with kiri:
            st.markdown(
                f'<div class="hasil-utama"><div class="label">Estimasi P0 · {nama_model[utama]}</div>'
                f'<div class="nilai">{angka(hasil[utama].estimasi)}<small>%</small></div></div>',
                unsafe_allow_html=True)
            baris = "".join(
                f'<tr class="{"utama" if k == utama else ""}"><td>{nama_model[k]}</td>'
                f'<td>{angka(v.estimasi)}%</td></tr>'
                for k, v in hasil.items() if v)
            baris += (f'<tr><td>P0 aktual BPS {tahun_acuan}'
                      f'{" (sebelum input diubah)" if diubah else ""}</td>'
                      f'<td>{angka(acuan.p0_aktual)}%</td></tr>')
            st.markdown(f'<table class="pembanding">{baris}</table>', unsafe_allow_html=True)

        with kanan:
            pilihan = [k for k, v in hasil.items() if v]
            jelaskan = st.segmented_control(
                "Kontribusi variabel menurut", pilihan, default=pilihan[0], key="rt_jelaskan",
                format_func=lambda k: nama_model[k].split(" (")[0]) or pilihan[0]
            hj = hasil[jelaskan]
            kontrib = sorted(hj.shap.items(), key=lambda x: abs(x[1]))
            fig = go.Figure(go.Bar(
                x=[v for _, v in kontrib], y=[self.label[f] for f, _ in kontrib], orientation="h",
                marker_color=[BATA if v > 0 else AKSEN for _, v in kontrib],
                text=[("+" if v > 0 else "") + angka(v) for _, v in kontrib],
                textposition="outside", cliponaxis=False,
                hovertemplate="%{y}: %{x:+.3f} poin persen<extra></extra>",
            ))
            fig.add_vline(x=0, line_color=REDUP, line_width=1)
            # ruang kosong di kiri & kanan agar label angka tidak menabrak nama variabel
            nilai_x = [v for _, v in kontrib]
            lo, hi = min(0, *nilai_x), max(0, *nilai_x)
            jarak = (hi - lo) or 1
            fig.update_xaxes(range=[lo - jarak * 0.22 if lo < 0 else 0, hi + jarak * 0.22])
            fig.update_layout(xaxis_title="Kontribusi terhadap estimasi (poin persen P0)",
                              margin=dict(l=12, r=24, t=10, b=12))
            grafik(fig, 300)
            catatan(f"Estimasi {angka(hj.estimasi)}% = nilai dasar model {angka(hj.nilai_dasar)}% "
                    "ditambah jumlah kontribusi keenam variabel (nilai SHAP CatBoost). "
                    "Merah menaikkan estimasi P0, hijau menurunkannya.")

    # ------------------------------------------------------- Kontribusi Variabel
    def tampilkan_kontribusi(self):
        kepala("Modul 3", "Kontribusi Variabel",
               "Seberapa besar dan ke arah mana tiap indikator memengaruhi estimasi P0 "
               "pada masing-masing model CatBoost.")
        kon = self.loader.load_kontribusi()
        model_ada = [m for m in NAMA_MODEL_KONTRIBUSI if m in set(kon.model)]
        pilih = st.segmented_control("Model", model_ada, default=model_ada[0], key="kon_model",
                                     format_func=NAMA_MODEL_KONTRIBUSI.get) or model_ada[0]
        k = kon[kon.model == pilih]

        c1, c2 = st.columns(2, gap="large")
        for kolom, nama_kolom, judul, sumbu, fmt in (
            (c1, "feature_importance", "Feature importance", "Kontribusi (%)", ".1f"),
            (c2, "mean_abs_shap", "Rata-rata |SHAP| pada data uji", "Poin persen P0", ".3f"),
        ):
            d = k.sort_values(nama_kolom)
            with kolom:
                st.markdown(f"### {judul}")
                fig = go.Figure(go.Bar(
                    x=d[nama_kolom], y=d.label, orientation="h", marker_color=AKSEN,
                    text=[angka(v, int(fmt[1])) for v in d[nama_kolom]],
                    textposition="outside", cliponaxis=False,
                    hovertemplate=f"%{{y}}: %{{x:{fmt}}}<extra></extra>"))
                fig.update_layout(xaxis_title=sumbu, margin=dict(l=12, r=64, t=10, b=12))
                grafik(fig, 300)
        catatan("<i>Feature importance</i> (PredictionValuesChange) menunjukkan rata-rata perubahan "
                "prediksi bila nilai variabel berubah, dinormalisasi menjadi 100%. "
                "Rata-rata |SHAP| menunjukkan besar kontribusi rata-rata tiap variabel "
                "terhadap estimasi pada data uji 2023–2024, dalam satuan poin persen P0.")

        st.markdown("## Arah pengaruh · model gabungan")
        df = self.loader.load_hasil_estimasi()
        df = df.join(self.predictor.shap_panel(df, "gabungan"))
        f = st.selectbox("Variabel", FITUR, format_func=self.label.get, key="kon_var")
        fig = go.Figure()
        for bag, warna, label in (("latih", "#9DB7B5", "Data latih"), ("uji", OKER, "Data uji")):
            b = df[df.data == bag]
            fig.add_scatter(x=b[f], y=b[f"shap_{f}"], mode="markers", name=label,
                            marker=dict(color=warna, size=6, opacity=0.75,
                                        line=dict(width=0.5, color="#FFFFFF")),
                            text=b.nama_kabkota + " " + b.tahun.astype(str),
                            hovertemplate="%{text}<br>nilai %{x:.2f} · SHAP %{y:+.3f}<extra></extra>")
        fig.add_hline(y=0, line_color=REDUP, line_width=1)
        fig.update_layout(xaxis_title=f"{self.label[f]} ({SATUAN[f]})",
                          yaxis_title="Nilai SHAP (poin persen P0)")
        grafik(fig, 380)
        catatan("Setiap titik adalah satu kabupaten/kota pada satu tahun. Titik di atas garis nol "
                "berarti nilai variabel tersebut menaikkan estimasi P0, di bawah garis menurunkannya.")

        st.markdown("## Model per kabupaten/kota")
        wil = self.loader.daftar_wilayah()
        nama = dict(zip(wil.kode_kabkota, wil.nama_kabkota))
        kode = st.selectbox("Kabupaten/kota", list(nama), format_func=nama.get, key="kon_wil")
        imp = self.predictor.importance(kode)
        met = self.loader.load_metrik_per_kabkota()
        m = met[met.kode_kabkota == kode]
        kiri, kanan = st.columns([1.5, 1], gap="large")
        with kiri:
            d = sorted(imp.items(), key=lambda x: x[1])
            fig = go.Figure(go.Bar(
                x=[v for _, v in d], y=[self.label[f] for f, _ in d], orientation="h",
                marker_color=AKSEN, text=[angka(v, 1) for _, v in d],
                textposition="outside", cliponaxis=False,
                hovertemplate="%{y}: %{x:.1f}%<extra></extra>"))
            fig.update_layout(xaxis_title="Feature importance (%)", margin=dict(l=12, r=64, t=10, b=12))
            grafik(fig, 300)
        with kanan:
            if len(m):
                r = m.iloc[0]
                st.markdown(_tabel_html(
                    ["Evaluasi data uji", "Nilai"],
                    [["RMSE", angka(r.RMSE, 3)], ["MAE", angka(r.MAE, 3)],
                     ["MAPE", angka(r["MAPE (%)"]) + "%"],
                     ["Baris latih / uji", f"{int(r.n_latih)} / {int(r.n_uji)}"],
                     ["Rentang P0 latih", f"{angka(r.p0_latih_min)} – {angka(r.p0_latih_max)}%"]],
                    kolom_angka=(1,)), unsafe_allow_html=True)
            catatan("Model per kab/kota hanya dilatih dengan 9 baris (2014–2022), "
                    "sehingga urutan kepentingan variabelnya bisa berbeda jauh antarwilayah.")

    # ---------------------------------------------------------------- Informasi
    def tampilkan_informasi(self):
        meta = self.meta
        kepala("Modul 4", "Informasi",
               "Cara kerja dashboard, metode pemodelan, sumber data, dan hasil evaluasi model.")
        tl, tu = meta["tahun_latih"], meta["tahun_uji"]

        kiri, kanan = st.columns([1.1, 1], gap="large")
        with kiri:
            st.markdown("## Cara kerja")
            st.markdown(f"""
<ol class="langkah">
<li><b>Pengumpulan data</b><span>Lima publikasi BPS tingkat kabupaten/kota, tahun {tl[0]}–{tu[1]}.</span></li>
<li><b>Penggabungan</b><span>Data disatukan dengan kunci <code>kode_kabkota</code> + <code>tahun</code>
menjadi panel 119 kabupaten/kota × 11 tahun.</span></li>
<li><b>Pembagian berdasarkan waktu</b><span>Data latih {tl[0]}–{tl[1]}, data uji {tu[0]}–{tu[1]}.
Tidak memakai pembagian acak agar model diuji pada tahun yang belum pernah dilihat.</span></li>
<li><b>Pencarian hiperparameter</b><span>Random search dengan validasi silang berurutan waktu,
hanya pada data latih.</span></li>
<li><b>Pelatihan &amp; evaluasi</b><span>Model gabungan, model kabupaten, model kota, dan satu model
per kabupaten/kota dievaluasi pada data uji dengan RMSE, MAE, MAPE, dan R².</span></li>
<li><b>Penyajian</b><span>Model final dan hasil estimasi disimpan, lalu dimuat oleh dashboard ini.</span></li>
</ol>""", unsafe_allow_html=True)
        with kanan:
            st.markdown("## Metode: CatBoost Regression")
            st.markdown(
                "CatBoost adalah algoritma *gradient boosting* berbasis pohon keputusan. "
                "Model dibangun bertahap: setiap pohon baru mempelajari sisa kesalahan dari "
                "pohon-pohon sebelumnya. CatBoost memakai pohon simetris (*oblivious trees*) "
                "dan regularisasi untuk mengurangi *overfitting*, serta dapat menangani "
                "nilai kosong secara langsung.\n\n"
                "Karena berbasis pohon, fitur tidak perlu dinormalisasi. Konsekuensinya, model "
                "tidak mengekstrapolasi: untuk nilai input di luar rentang data latih, estimasi "
                "cenderung mendatar pada nilai terdekat yang pernah dipelajari.")
            st.markdown("Kontribusi tiap variabel pada satu estimasi dihitung dengan nilai SHAP "
                        "bawaan CatBoost.")

        st.markdown("## Sumber data")
        # Satu baris per publikasi BPS; variabel dari publikasi yang sama digabung
        var = self.loader.load_variabel()
        sumber = [
            (html.escape(pub),
             ", ".join(f"<code>{k}</code>" for k in g["kode_variabel"])
             + (" (target)" if (g["peran"] == "target").all() else ""),
             html.escape(g["satuan"].iloc[0]))
            for pub, g in var.groupby("sumber", sort=False)
        ]
        st.markdown(_tabel_html(["Publikasi BPS", "Variabel", "Satuan"], sumber), unsafe_allow_html=True)
        catatan("AHH dan pengeluaran per kapita dipakai terpisah untuk laki-laki dan perempuan, "
                "sehingga model memiliki enam variabel prediktor.")

        st.markdown("## Evaluasi pada data uji")
        met = self.loader.load_metrik()
        st.markdown(_tabel_html(
            ["Model", "RMSE", "MAE", "MAPE (%)", "R²", "n"],
            [[html.escape(r["model"]), angka(r["RMSE"], 3), angka(r["MAE"], 3),
              angka(r["MAPE (%)"], 2), angka(r["R2"], 3), int(r["n"])] for _, r in met.iterrows()],
            kolom_angka=(1, 2, 3, 4, 5)), unsafe_allow_html=True)
        mk = self.loader.load_metrik_per_kabkota()
        n_luar = int(mk.di_luar_rentang_latih.sum())
        catatan(f"RMSE dan MAE dalam poin persen P0; n = jumlah baris uji. "
                f"Baris “gabungan — subset” adalah model gabungan yang dievaluasi hanya pada kabupaten "
                f"atau kota, agar sebanding dengan model per jenis. Metrik model per kab/kota dihitung "
                f"dari gabungan prediksi 119 model yang masing-masing hanya memprediksi wilayahnya "
                f"sendiri. Pada {n_luar} dari {len(mk)} wilayah, P0 aktual tahun uji berada di luar "
                f"rentang P0 data latihnya.")

        st.markdown("## Hiperparameter terpilih")
        hp = meta["hiperparameter"]
        nama_hp = ["iterations", "depth", "learning_rate", "l2_leaf_reg", "random_strength"]
        judul = {"gabungan": "Gabungan", "kabupaten": "Kabupaten", "kota": "Kota",
                 "per_kabkota": "Per kab/kota"}
        st.markdown(_tabel_html(
            ["Model"] + [f"<code>{n}</code>" for n in nama_hp],
            [[judul.get(m, m)] + [str(v.get(n, "–")) for n in nama_hp] for m, v in hp.items()],
            kolom_angka=tuple(range(1, len(nama_hp) + 1))), unsafe_allow_html=True)

        versi = meta.get("versi", {})
        if versi:
            catatan("Dilatih dengan " + " · ".join(f"{k} {v}" for k, v in versi.items()) + ".")
