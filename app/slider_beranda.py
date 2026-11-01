import base64
from pathlib import Path

import streamlit as st

ASET = Path(__file__).resolve().parent / "assets" / "beranda"
MERAH_SDG1 = "#E5243B"

# Foto dari Wikimedia Commons; rincian lisensi ada di assets/beranda/SUMBER.md
FOTO = [
    ("02_tepi_rel.jpg", "Permukiman di tepi rel kereta, Jakarta",
     "Hunian semipermanen di sepanjang jalur kereta di tengah kota.",
     "Foto: Hariadhi · CC BY-SA 4.0 · Wikimedia Commons"),
    ("03_kanal.jpg", "Permukiman di sepanjang kanal, Jakarta",
     "Rumah-rumah padat berdiri rapat di kedua sisi bantaran kanal.",
     "Foto: Jimmy McIntyre · CC BY-SA 2.0 · Wikimedia Commons"),
    ("04_petani.jpg", "Petani memanen kacang tanah, Indonesia",
     "Kehidupan petani di perdesaan, wajah lain dari wilayah kabupaten.",
     "Foto: DFAT Australia · CC BY 2.0 · Wikimedia Commons"),
    ("05_tepi_sungai_1975.jpg", "Permukiman di tepi sungai, Jakarta, 1975",
     "Foto arsip permukiman padat di bantaran sungai, hampir lima dekade lalu.",
     "Foto: Pál Baross · CC BY-SA 3.0 · Wikimedia Commons"),
]


def _data_uri(nama):
    jenis = "png" if nama.endswith(".png") else "jpeg"
    isi = base64.b64encode((ASET / nama).read_bytes()).decode()
    return f"data:image/{jenis};base64,{isi}"


@st.cache_data(show_spinner=False)
def logo_sdg1():
    """Logo SDG 1 sebagai data URI (dipakai juga di sidebar)."""
    return _data_uri("01_sdg1.png")


@st.cache_data(show_spinner=False)
def _html_slider():
    slide_sdg = f"""
    <div class="slide sdg">
      <img class="logo" src="{logo_sdg1()}" alt="Logo SDG 1: No Poverty">
      <div class="teks">
        <div class="rubrik">Tujuan Pembangunan Berkelanjutan</div>
        <h2>Tujuan 1 · Tanpa Kemiskinan</h2>
        <p>Mengakhiri kemiskinan dalam segala bentuk di mana pun.</p>
        <p class="kecil">Indikator 1.2.1 SDGs adalah persentase penduduk yang hidup di bawah garis
        kemiskinan nasional, yaitu P0 yang dimodelkan pada dashboard ini.</p>
        <div class="kredit">Logo: Perserikatan Bangsa-Bangsa</div>
      </div>
    </div>"""
    slide_foto = "".join(f"""
    <div class="slide foto">
      <img src="{_data_uri(f)}" alt="{judul}">
      <div class="keterangan"><h3>{judul}</h3><p>{teks}</p><div class="kredit">{kredit}</div></div>
    </div>""" for f, judul, teks, kredit in FOTO)
    n = 1 + len(FOTO)

    return f"""
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500&family=Source+Serif+4:opsz,wght@8..60,600&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; margin: 0; }}
  body {{ background: transparent; font-family: 'IBM Plex Sans', system-ui, sans-serif; }}
  .bingkai {{ position: relative; height: 360px; overflow: hidden; border-radius: 4px; background: #1E2124; }}
  .jalur {{ display: flex; height: 100%; transition: transform .7s cubic-bezier(.65,0,.35,1); }}
  .slide {{ position: relative; flex: 0 0 100%; height: 100%; }}
  .foto img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
  .keterangan {{ position: absolute; left: 0; bottom: 0; max-width: 520px; margin: 0 0 22px 22px;
      background: rgba(30,33,36,.86); color: #F5F3EE; padding: 14px 18px 12px; border-left: 3px solid {MERAH_SDG1}; }}
  .keterangan h3 {{ font-family: 'Source Serif 4', Georgia, serif; font-size: 19px; font-weight: 600; }}
  .keterangan p {{ font-size: 13.5px; line-height: 1.5; margin-top: 4px; color: #DAD6CE; }}
  .kredit {{ font-family: 'IBM Plex Mono', monospace; font-size: 10.5px; letter-spacing: .02em;
      margin-top: 8px; opacity: .7; }}
  .sdg {{ background: {MERAH_SDG1}; color: #FFF; display: flex; align-items: center; gap: 40px; padding: 0 56px; }}
  .sdg .logo {{ height: 250px; width: 250px; flex: 0 0 auto; outline: 2px solid rgba(255,255,255,.35); outline-offset: 6px; }}
  .sdg .rubrik {{ font-family: 'IBM Plex Mono', monospace; font-size: 12px; letter-spacing: .12em;
      text-transform: uppercase; opacity: .85; }}
  .sdg h2 {{ font-family: 'Source Serif 4', Georgia, serif; font-size: 34px; font-weight: 600; line-height: 1.15; margin: 8px 0 10px; }}
  .sdg p {{ font-size: 16px; line-height: 1.55; max-width: 52ch; }}
  .sdg p.kecil {{ font-size: 13.5px; opacity: .88; margin-top: 10px; }}
  .kendali {{ position: absolute; right: 18px; bottom: 22px; display: flex; gap: 6px; }}
  .kendali button {{ width: 36px; height: 36px; border: 1px solid rgba(255,255,255,.45); background: rgba(30,33,36,.55);
      color: #FFF; cursor: pointer; display: grid; place-items: center; border-radius: 3px; }}
  .kendali button:hover {{ background: rgba(30,33,36,.85); }}
  .penanda {{ position: absolute; left: 22px; right: 120px; top: 16px; display: flex; gap: 6px; }}
  .penanda span {{ flex: 1; height: 3px; background: rgba(255,255,255,.35); cursor: pointer; overflow: hidden; }}
  .penanda span i {{ display: block; height: 100%; width: 0; background: #FFF; }}
  .penanda span.aktif i {{ animation: isi var(--durasi) linear forwards; }}
  .penanda span.lewat i {{ width: 100%; }}
  .bingkai:hover .penanda span.aktif i {{ animation-play-state: paused; }}
  @keyframes isi {{ to {{ width: 100%; }} }}
  @media (max-width: 700px) {{
    .sdg {{ padding: 0 22px; gap: 18px; }}
    .sdg .logo {{ height: 110px; width: 110px; }}
    .sdg h2 {{ font-size: 22px; }} .sdg p.kecil {{ display: none; }}
    .keterangan {{ margin: 0; max-width: none; right: 0; }}
    .kendali {{ bottom: auto; top: 30px; }}
  }}
</style>
<div class="bingkai" id="bingkai" style="--durasi: 6s">
  <div class="jalur" id="jalur">{slide_sdg}{slide_foto}</div>
  <div class="penanda" id="penanda">{"<span><i></i></span>" * n}</div>
  <div class="kendali">
    <button id="mundur" aria-label="Slide sebelumnya"><svg width="16" height="16" viewBox="0 0 16 16"><path d="M10 3 5 8l5 5" fill="none" stroke="currentColor" stroke-width="1.8"/></svg></button>
    <button id="maju" aria-label="Slide berikutnya"><svg width="16" height="16" viewBox="0 0 16 16"><path d="m6 3 5 5-5 5" fill="none" stroke="currentColor" stroke-width="1.8"/></svg></button>
  </div>
</div>
<script>
  const n = {n}, jalur = document.getElementById('jalur'), bingkai = document.getElementById('bingkai');
  const tanda = [...document.querySelectorAll('#penanda span')];
  let i = 0;
  function ke(k) {{
    i = (k + n) % n;
    jalur.style.transform = `translateX(-${{i * 100}}%)`;
    tanda.forEach((t, j) => {{
      t.className = j < i ? 'lewat' : '';
      const isi = t.firstChild; isi.style.animation = 'none'; isi.offsetWidth; isi.style.animation = '';
      if (j === i) t.className = 'aktif';
    }});
  }}
  // pindah otomatis saat animasi penanda aktif selesai (ikut berhenti ketika kursor di atas slider)
  tanda.forEach((t, j) => t.firstChild.addEventListener('animationend', () => {{ if (j === i) ke(i + 1); }}));
  tanda.forEach((t, j) => t.addEventListener('click', () => ke(j)));
  document.getElementById('maju').onclick = () => ke(i + 1);
  document.getElementById('mundur').onclick = () => ke(i - 1);
  let x0 = null;
  bingkai.addEventListener('touchstart', e => x0 = e.touches[0].clientX, {{passive: true}});
  bingkai.addEventListener('touchend', e => {{
    if (x0 === null) return;
    const dx = e.changedTouches[0].clientX - x0;
    if (Math.abs(dx) > 40) ke(i + (dx < 0 ? 1 : -1));
    x0 = null;
  }});
  ke(0);
</script>
"""


def tampilkan_slider():
    st.iframe(_html_slider(), height=364)
