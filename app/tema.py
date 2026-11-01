import html

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

# Palet
KERTAS = "#F5F3EE"
PANEL = "#ECE8E0"
TINTA = "#1E2124"
REDUP = "#676B70"
GARIS = "#DDD8CE"
AKSEN = "#0F5257"   # estimasi / model
OKER = "#B7791F"    # penanda periode uji
BATA = "#A23B2A"    # kontribusi menaikkan P0
AKTUAL = "#2B2D31"  # data aktual BPS

WARNA_PROVINSI = {
    "DKI Jakarta": "#0F5257",
    "Jawa Barat": "#B7791F",
    "Jawa Tengah": "#A23B2A",
    "DI Yogyakarta": "#3E6B9A",
    "Jawa Timur": "#6B8E4E",
    "Banten": "#7A5C8E",
}

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,500;8..60,600&display=swap');

.stApp {{ background: {KERTAS}; color: {TINTA}; }}
.stApp, .stApp p, .stApp li, .stApp label, .stApp input, .stApp button,
.stApp textarea, .stApp td, .stApp th {{
    font-family: 'IBM Plex Sans', system-ui, sans-serif;
}}
.stApp h1, .stApp h2, .stApp h3, .stApp h4 {{
    font-family: 'Source Serif 4', Georgia, serif;
    font-weight: 600;
    letter-spacing: -0.01em;
    color: {TINTA};
}}
.stApp h2 {{ font-size: 1.45rem; margin-top: .6rem; }}
.stApp h3 {{ font-size: 1.15rem; }}

[data-testid="stHeader"] {{ background: transparent; }}
footer {{ visibility: hidden; }}
.block-container {{ padding-top: 2.2rem; padding-bottom: 4rem; max-width: 1180px; }}

/* Sidebar */
[data-testid="stSidebar"] {{ background: {PANEL}; border-right: 1px solid {GARIS}; }}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{ gap: .3rem; }}
[data-testid="stSidebarContent"] {{ padding-top: .4rem; }}
[data-testid="stSidebar"] .stButton button {{
    justify-content: flex-start; border: 1px solid transparent; background: transparent;
    color: {TINTA}; padding: .5rem .75rem; min-height: 2.6rem; border-radius: 4px; font-weight: 500;
}}
[data-testid="stSidebar"] .stButton button > div {{ justify-content: flex-start; gap: .6rem; }}
[data-testid="stSidebar"] .stButton button:hover {{ background: rgba(30,33,36,.06); color: {TINTA}; border-color: transparent; }}
[data-testid="stSidebar"] .stButton button[kind="primary"],
[data-testid="stSidebar"] .stButton button[data-testid="stBaseButton-primary"] {{
    background: {AKSEN}; color: #FFFFFF; border-color: {AKSEN};
}}
[data-testid="stSidebar"] .stButton button:focus:not(:active) {{ color: inherit; border-color: transparent; }}
.merek {{ display: flex; gap: .8rem; align-items: center; padding: .2rem 0 1.1rem;
    border-bottom: 1px solid {GARIS}; margin-bottom: .6rem; }}
.merek img {{ width: 52px; height: 52px; flex: 0 0 auto; border-radius: 2px; }}
.merek .kode {{ font-family: 'IBM Plex Mono', monospace; font-size: .68rem;
    letter-spacing: .08em; text-transform: uppercase; color: {REDUP}; }}
.merek .nama {{ font-family: 'Source Serif 4', Georgia, serif; font-size: 1.08rem;
    font-weight: 600; line-height: 1.25; margin-top: .15rem; }}
.judul-sb {{ font-family: 'IBM Plex Mono', monospace; font-size: .68rem; letter-spacing: .1em;
    text-transform: uppercase; color: {REDUP}; margin: 1.1rem 0 .45rem; }}
.ringkas-sb {{ display: grid; grid-template-columns: 1fr 1fr; border-top: 1px solid {TINTA}; }}
.ringkas-sb > div {{ padding: .55rem .2rem .5rem 0; border-bottom: 1px solid {GARIS}; }}
.ringkas-sb > div:nth-child(even) {{ padding-left: .7rem; border-left: 1px solid {GARIS}; }}
.ringkas-sb b {{ display: block; font-family: 'Source Serif 4', Georgia, serif; font-size: 1.35rem;
    font-weight: 600; line-height: 1.1; font-variant-numeric: tabular-nums; }}
.ringkas-sb span {{ font-size: .74rem; color: {REDUP}; }}
.terbaik-sb {{ background: #F7F5F0; border: 1px solid {GARIS}; border-left: 3px solid {AKSEN};
    border-radius: 3px; padding: .65rem .8rem; font-size: .8rem; line-height: 1.5; }}
.terbaik-sb .nm {{ font-weight: 600; }}
.terbaik-sb .ang {{ display: flex; gap: 1rem; margin-top: .3rem; font-family: 'IBM Plex Mono', monospace;
    font-size: .78rem; }}
.terbaik-sb .ang span {{ color: {REDUP}; }}
.kaki-sidebar {{ font-size: .74rem; color: {REDUP}; line-height: 1.55;
    border-top: 1px solid {GARIS}; padding-top: .8rem; margin-top: 1.3rem; }}

/* Kepala halaman */
.kepala {{ border-bottom: 1px solid {GARIS}; padding-bottom: 1.1rem; margin-bottom: 1.4rem; }}
.kepala .rubrik {{ font-family: 'IBM Plex Mono', monospace; font-size: .74rem;
    letter-spacing: .1em; text-transform: uppercase; color: {AKSEN}; }}
.kepala h1 {{ font-size: 2.1rem; line-height: 1.15; margin: .35rem 0 .5rem; padding: 0; }}
.stApp h1 a, .stApp h2 a, .stApp h3 a {{ display: none; }}
.kepala p {{ color: {REDUP}; max-width: 68ch; font-size: 1rem; line-height: 1.6; margin: 0; }}

/* Deret angka ringkas */
.deret-angka {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
    border-top: 2px solid {TINTA}; margin: .4rem 0 1.6rem; }}
.deret-angka > div {{ padding: .8rem 1rem .6rem 0; }}
.deret-angka > div + div {{ padding-left: 1rem; border-left: 1px solid {GARIS}; }}
.deret-angka .label {{ font-size: .78rem; color: {REDUP}; }}
.deret-angka .nilai {{ font-family: 'Source Serif 4', Georgia, serif; font-size: 1.9rem;
    font-weight: 600; font-variant-numeric: tabular-nums; line-height: 1.2; margin-top: .15rem; }}
.deret-angka .nilai small {{ font-size: .95rem; font-weight: 500; color: {REDUP}; margin-left: .15rem; }}
.deret-angka .ket {{ font-size: .76rem; color: {REDUP}; margin-top: .1rem; }}

/* Catatan & peringatan */
.catatan {{ font-size: .84rem; color: {REDUP}; border-left: 2px solid {OKER};
    padding: .15rem 0 .15rem .8rem; margin: .6rem 0 1rem; line-height: 1.55; }}
.peringatan {{ background: #FBF3E4; border: 1px solid #EBD6AE; border-radius: 4px;
    padding: .7rem .9rem; font-size: .86rem; line-height: 1.55; margin: .6rem 0; }}
.peringatan ul {{ margin: .3rem 0 0 1.1rem; padding: 0; }}

/* Langkah bernomor */
.langkah {{ counter-reset: no; list-style: none; padding: 0; margin: 0; }}
.langkah li {{ counter-increment: no; position: relative; padding: .75rem 0 .75rem 2.6rem;
    border-bottom: 1px solid {GARIS}; line-height: 1.55; }}
.langkah li::before {{ content: counter(no, decimal-leading-zero); position: absolute; left: 0; top: .8rem;
    font-family: 'IBM Plex Mono', monospace; font-size: .8rem; color: {AKSEN}; }}
.langkah li b {{ display: block; font-weight: 600; }}
.langkah li span {{ color: {REDUP}; font-size: .9rem; }}

/* Hasil estimasi real-time */
.hasil-utama {{ border-top: 2px solid {AKSEN}; padding-top: .7rem; }}
.hasil-utama .label {{ font-size: .8rem; color: {REDUP}; }}
.hasil-utama .nilai {{ font-family: 'Source Serif 4', Georgia, serif; font-size: 3.2rem;
    font-weight: 600; color: {AKSEN}; line-height: 1.1; font-variant-numeric: tabular-nums; }}
.hasil-utama .nilai small {{ font-size: 1.4rem; color: {REDUP}; font-weight: 500; }}
.pembanding {{ width: 100%; border-collapse: collapse; margin-top: .9rem; font-size: .88rem; }}
.pembanding td {{ padding: .45rem 0; border-bottom: 1px solid {GARIS}; }}
.pembanding td:last-child {{ text-align: right; font-family: 'IBM Plex Mono', monospace;
    font-variant-numeric: tabular-nums; }}
.pembanding tr.utama td {{ font-weight: 600; color: {AKSEN}; }}

/* Tabel info sederhana */
.tabel-info {{ width: 100%; border-collapse: collapse; font-size: .88rem; margin: .4rem 0 1.2rem; }}
.tabel-info th {{ text-align: left; font-weight: 600; font-size: .78rem; color: {REDUP};
    border-bottom: 1px solid {TINTA}; padding: .45rem .6rem .45rem 0; }}
.tabel-info td {{ border-bottom: 1px solid {GARIS}; padding: .5rem .6rem .5rem 0; vertical-align: top; }}
.tabel-info td.angka {{ font-family: 'IBM Plex Mono', monospace; text-align: right;
    font-variant-numeric: tabular-nums; }}
.tabel-info th.angka {{ text-align: right; }}
.tabel-info code {{ font-family: 'IBM Plex Mono', monospace; font-size: .8rem;
    background: {PANEL}; padding: .05rem .3rem; border-radius: 3px; }}

/* Kontrol input */
[data-baseweb="input"], [data-baseweb="select"] > div, [data-baseweb="base-input"] {{
    border-radius: 4px !important; background: #FFFFFF;
}}
.stButton button, [data-testid="stFormSubmitButton"] button, [data-testid="stDownloadButton"] button {{
    border-radius: 4px; font-weight: 500;
}}
[data-testid="stFormSubmitButton"] button {{
    background: {AKSEN}; border-color: {AKSEN}; color: #FFFFFF; padding: .45rem 1.6rem;
}}
[data-testid="stFormSubmitButton"] button:hover {{ background: #0B3F43; border-color: #0B3F43; color: #FFFFFF; }}
[data-testid="stForm"] {{ border: 1px solid {GARIS}; border-radius: 4px; background: #FBFAF7; }}
.stTabs [data-baseweb="tab-list"] {{ gap: 1.6rem; border-bottom: 1px solid {GARIS}; }}
.stTabs [data-baseweb="tab"] {{ padding-left: 0; padding-right: 0; }}
</style>
"""


def terapkan_tema():
    """Pasang CSS dan jadikan template Plotly 'p0' sebagai bawaan."""
    st.markdown(CSS, unsafe_allow_html=True)
    pio.templates["p0"] = go.layout.Template(layout=dict(
        font=dict(family="IBM Plex Sans, system-ui, sans-serif", size=13, color=TINTA),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorway=list(WARNA_PROVINSI.values()),
        separators=",.",
        margin=dict(l=12, r=16, t=40, b=12),
        # automargin: ruang untuk label sumbu dihitung otomatis agar tidak terpotong
        xaxis=dict(showgrid=False, zeroline=False, linecolor=GARIS, ticks="outside",
                   tickcolor=GARIS, automargin=True, title=dict(font=dict(size=12, color=REDUP))),
        yaxis=dict(gridcolor="#E4DFD5", zeroline=False, showline=False, automargin=True,
                   ticksuffix="  ", title=dict(font=dict(size=12, color=REDUP))),
        legend=dict(orientation="h", x=0, y=1.02, yanchor="bottom",
                    bgcolor="rgba(0,0,0,0)", font=dict(size=12)),
        hoverlabel=dict(bgcolor="#FFFFFF", bordercolor=GARIS,
                        font=dict(family="IBM Plex Sans, sans-serif", color=TINTA)),
    ))
    pio.templates.default = "p0"


def grafik(fig, tinggi=380):
    """Tampilkan grafik Plotly dengan tema sendiri (bukan tema bawaan Streamlit).

    Zoom dan geser dimatikan supaya grafik tidak bisa 'hilang' karena ter-zoom tanpa sengaja;
    tooltip saat kursor di atas grafik tetap berfungsi.
    """
    # Font dan warna latar ditulis langsung di layout: frontend Streamlit menimpa nilai yang
    # hanya ada di template dengan font & warna temanya sendiri (meski theme=None).
    fig.update_layout(
        height=tinggi, dragmode=False,
        font=dict(family="IBM Plex Sans, Segoe UI, system-ui, sans-serif", size=13, color=TINTA),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(fixedrange=True, automargin=True)
    fig.update_yaxes(fixedrange=True, automargin=True)
    st.plotly_chart(fig, theme=None, config={
        "displayModeBar": False, "scrollZoom": False, "doubleClick": False,
    })


def angka(x, d=2):
    """Format angka gaya Indonesia: 1.234,56."""
    if x is None or x != x:  # None atau NaN
        return "–"
    teks = f"{x:,.{d}f}"
    return teks.replace(",", " ").replace(".", ",").replace(" ", ".")


def kepala(rubrik, judul, deskripsi=""):
    st.markdown(
        f'<div class="kepala"><div class="rubrik">{html.escape(rubrik)}</div>'
        f'<h1>{html.escape(judul)}</h1><p>{deskripsi}</p></div>',
        unsafe_allow_html=True,
    )


def deret_angka(item):
    """item: daftar (label, nilai, satuan, keterangan)."""
    isi = "".join(
        f'<div><div class="label">{lbl}</div>'
        f'<div class="nilai">{nilai}<small>{satuan}</small></div>'
        f'<div class="ket">{ket}</div></div>'
        for lbl, nilai, satuan, ket in item
    )
    st.markdown(f'<div class="deret-angka">{isi}</div>', unsafe_allow_html=True)


def catatan(teks):
    st.markdown(f'<div class="catatan">{teks}</div>', unsafe_allow_html=True)
