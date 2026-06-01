"""
app.py — Streamlit App
──────────────────────
Website Rekomendasi Menu Diet Zone menggunakan Algoritma Genetika
dengan Knowledge-Based Constraint.

Menjawab Rumusan Masalah 2:
  (a) Constrained Initialization
  (b) Directed Mutation

Jalankan: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import time
import math
from typing import List

from db_connector import (
    get_connection, test_connection,
    load_all_pools, load_threshold
)
from genetic_algorithm import (
    KnowledgeBase, AlgoritmaGenetika,
    WaktuMakan, hitung_rata_gizi, hitung_fitness,
    verifikasi_constraint, THRESHOLD, GEN_WAKTU_MAP
)

from evaluation import (
    run_ag, evaluasi_komparatif,
    validasi_ketercapaian_gizi, validasi_relevansi_menu,
    bandingkan_menu, rangkuman_evaluasi
)

# ═══════════════════════════════════════════════════════════════════
# KONFIGURASI HALAMAN
# ═══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Diet Zone - Algoritma Genetika Kelompok 4A",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────
st.markdown("""
<style>
    .metric-card {
        background: #f8f9fa;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
        margin: 4px;
    }
    .metric-label { font-size: 12px; color: #666; margin-bottom: 4px; }
    .metric-value { font-size: 22px; font-weight: 600; color: #1a1a2e; }
    .valid-badge  { background:#d4edda; color:#155724;
                    padding:2px 8px; border-radius:12px; font-size:12px; }
    .invalid-badge{ background:#f8d7da; color:#721c24;
                    padding:2px 8px; border-radius:12px; font-size:12px; }
    .waktu-pagi   { color:#000000; background:#fff3cd; padding:4px 10px;
                    border-radius:6px; font-weight:600; font-size:13px; }
    .waktu-siang  { color:#000000; background:#cce5ff; padding:4px 10px;
                    border-radius:6px; font-weight:600; font-size:13px; }
    .waktu-malam  { color:#000000; background:#d1ecf1; padding:4px 10px;
                    border-radius:6px; font-weight:600; font-size:13px; }
    .section-header {
        font-size: 18px; font-weight: 600;
        border-left: 4px solid #1a1a2e;
        padding-left: 12px; margin: 20px 0 12px 0;
    }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════════════
for key, val in {
    "kb":                    None,
    "db_config":             None,
    "db_connected":          False,
    "hasil_7_hari":          None,
    "history_best":          [],
    "history_avg":           [],
    "hasil_kb":              None,
    "hasil_standar":         None,
    "hist_best_kb":          [],
    "hist_avg_kb":           [],
    "hasil_komparatif":      None,
    "validasi_gizi_kb":      None,
    "validasi_relevansi_kb": None,
    "validasi_gizi_std":     None,
    "validasi_relavansi_std":None,
    "perbandingan_menu":     None,
    "rangkuman":             None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = val


# ═══════════════════════════════════════════════════════════════════
# SIDEBAR — KONFIGURASI
# ═══════════════════════════════════════════════════════════════════
with st.sidebar:
    html_title = """
        <h1 style="display: flex; align-items: center; gap: 10px;">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-6">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 0 1 0 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 0 1-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 0 1-1.369-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 0 1 0-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28Z" />
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
            </svg>
            Konfigurasi
        </h1>
    """

    st.markdown(html_title, unsafe_allow_html=True)

    html_connection = """
        <h1 style="display: flex; align-items: center; gap: 10px;">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-6">
            <path stroke-linecap="round" stroke-linejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 0v3.75m-16.5-3.75v3.75m16.5 0v3.75C20.25 16.153 16.556 18 12 18s-8.25-1.847-8.25-4.125v-3.75m16.5 0c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125" />
            </svg>
            Koneksi Database
        </h1>
    """
    st.markdown(html_connection, unsafe_allow_html=True)
    db_host = st.text_input("Host", value="localhost")
    db_port = st.number_input("Port", value=3306, min_value=1, max_value=65535)
    db_name = st.text_input("Database", value="diet_zone")
    db_user = st.text_input("User", value="root")
    db_pass = st.text_input("Password", value="", type="password")

    db_config = {
        "host": db_host, "port": int(db_port),
        "database": db_name, "user": db_user, "password": db_pass,
    }

    if st.button("Test & Hubungkan", use_container_width=True):
        with st.spinner("Menghubungkan..."):
            ok, msg = test_connection(db_config)
        if ok:
            st.success(msg)
            st.session_state.db_config    = db_config
            st.session_state.db_connected = True
            # Load knowledge base
            conn   = get_connection(db_config)
            pools  = load_all_pools(conn)
            conn.close()
            kb = KnowledgeBase()
            kb.load_from_dataframes(
                pools["breakfast"], pools["lunch"], pools["dinner"]
            )
            st.session_state.kb = kb
            info = kb.info()
            st.info(f"Pool: B={info['S_breakfast']} | L={info['S_lunch']} | D={info['S_dinner']}")
        else:
            st.error(f"Gagal: {msg}")
            st.session_state.db_connected = False

    st.divider()

    # ── Parameter AG ──────────────────────────────────────────────
    st.markdown("### Parameter Algoritma Genetika")
    pop_size      = st.slider("Ukuran Populasi",   10, 200, 70,  10)
    n_generasi    = st.slider("Jumlah Generasi",   50, 1000, 800, 50)
    crossover_rate= st.slider("Crossover Rate",    0.1, 1.0, 0.8, 0.05)
    mutation_rate = st.slider("Mutation Rate",     0.01, 0.5, 0.1, 0.01)
    n_hari        = st.slider("Jumlah Hari",       1, 7, 7, 1)

    st.divider()
    st.markdown("""
    **Referensi:**
    Yuliastuti et al. (2024)
    *Teknika 13(1):18-26*

    **Threshold Diet Zone:**
    - Karbo: **40%**
    - Protein: **30%**
    - Lemak: **30%**
    - Serat: **≥8,33 g/waktu**
    """)

    st.divider()
    st.markdown("### Parameter Evaluasi")
    n_run_eval = st.slider("Jumlah Run Eksperimen", 3, 10, 5, 1)
    n_gen_eval = st.slider("Generasi (Evaluasi)",  50, 1000, 100, 50)
    st.caption("Gunakan generasi lebih kecil untuk evaluasi cepat")


# ═══════════════════════════════════════════════════════════════════
# HEADER UTAMA
# ═══════════════════════════════════════════════════════════════════
st.title("Rekomendasi Menu Diet Zone - Kelompok 4A")
st.markdown("**Algoritma Genetika dengan Knowledge-Based Constraint**")
st.markdown("---")

if 'hasil' not in st.session_state:
    st.session_state.hasil = []

len_day = len(st.session_state.hasil)
title_tab2 = f"Hasil Menu {len_day} Hari" if len_day > 0 else "Hasil Menu"

# ═══════════════════════════════════════════════════════════════════
# TAB UTAMA
# ═══════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Jalankan AG",
    title_tab2,
    "Analisis Fitness",
    "Verifikasi Constraint",
    "Evaluasi"
])


# ─────────────────────────────────────────────────────────────────
# TAB 1 — JALANKAN AG
# ─────────────────────────────────────────────────────────────────
with tab1:
    st.markdown('<div class="section-header">Constrained Initialization & Directed Mutation</div>',
                unsafe_allow_html=True)

    # Penjelasan mekanisme
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("""
        #### (a) Constrained Initialization
        Gen dibangkitkan HANYA dari subhimpunan waktu makan:
        | Gen | Posisi | Sumber Pool |
        |-----|--------|-------------|
        | g1, g2, g3 | Makan Pagi | S_breakfast |
        | g4, g5, g6 | Makan Siang | S_lunch |
        | g7, g8, g9 | Makan Malam | S_dinner |

        Berbeda dengan Yuliastuti et al. (2024) yang memilih
        gen secara acak dari seluruh 340 data tanpa batasan.
        """)
    with col_b:
        st.markdown("""
        #### (b) Directed Mutation
        Gen yang dimutasi **hanya diganti** dari subhimpunan
        waktu makan yang SAMA dengan posisi gen tersebut.

        ```
        posisi 0,1,2 → pengganti dari S_breakfast
        posisi 3,4,5 → pengganti dari S_lunch
        posisi 6,7,8 → pengganti dari S_dinner
        ```

        Memastikan kromosom hasil mutasi tetap valid
        secara domain waktu makan.
        """)

    st.divider()

    # Status KB
    if st.session_state.kb is None:
        st.warning("Hubungkan database terlebih dahulu melalui sidebar kiri.")
    else:
        kb   = st.session_state.kb
        info = kb.info()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("S_breakfast", f"{info['S_breakfast']} item", "Pool Makan Pagi")
        col2.metric("S_lunch",     f"{info['S_lunch']} item",     "Pool Makan Siang")
        col3.metric("S_dinner",    f"{info['S_dinner']} item",    "Pool Makan Malam")
        col4.metric("Total",
                    f"{info['S_breakfast']+info['S_lunch']+info['S_dinner']} relasi",
                    "bahan_waktu_makan")

        st.divider()

        if st.button("▶ Jalankan Algoritma Genetika", type="primary",
                     use_container_width=True):

            progress_bar  = st.progress(0)
            status_text   = st.empty()
            live_metric   = st.empty()
            total_steps   = n_hari * n_generasi
            step_counter  = [0]
            hist_best_all = []
            hist_avg_all  = []

            def callback(hari, generasi, best, avg):
                step_counter[0] += 1
                pct = step_counter[0] / total_steps
                progress_bar.progress(min(pct, 1.0))
                status_text.markdown(
                    f"**Hari {hari}/{n_hari}** — Generasi {generasi}/{n_generasi} "
                    f"| Best fitness: `{best:.4f}` | Avg: `{avg:.4f}`"
                )
                hist_best_all.append(best)
                hist_avg_all.append(avg)
                if generasi % 50 == 0:
                    live_metric.line_chart(
                        pd.DataFrame({"Best": hist_best_all, "Rata-rata": hist_avg_all}),
                        height=200
                    )

            ag = AlgoritmaGenetika(
                kb=kb,
                pop_size=pop_size,
                n_generasi=n_generasi,
                crossover_rate=crossover_rate,
                mutation_rate=mutation_rate,
                n_hari=n_hari,
            )

            start = time.time()
            hasil = ag.run(callback=callback)

            elapsed = time.time() - start

            progress_bar.progress(1.0)
            status_text.success(f"Selesai dalam {elapsed:.1f} detik!")

            st.session_state.hasil_7_hari = hasil
            st.session_state.history_best = hist_best_all
            st.session_state.history_avg  = hist_avg_all

            # Rangkuman hasil
            st.divider()
            fitness_vals = [k.fitness for k in hasil]
            c1, c2, c3 = st.columns(3)
            c1.metric("Fitness Terbaik",  f"{min(fitness_vals):.4f}")
            c2.metric("Fitness Rata-rata", f"{sum(fitness_vals)/len(fitness_vals):.4f}")
            c3.metric("Baseline (2024)",   "15.54",
                      delta=f"{min(fitness_vals)-15.54:.4f}",
                      delta_color="inverse")

            st.info(f"Lihat hasil lengkap di tab **Hasil Menu {len(hasil)} Hari**")


# ─────────────────────────────────────────────────────────────────
# TAB 2 — HASIL MENU 7 HARI
# ─────────────────────────────────────────────────────────────────
with tab2:
    if st.session_state.hasil_7_hari is None:
        st.info("Jalankan Algoritma Genetika terlebih dahulu di tab pertama.")
    else:
        hasil = st.session_state.hasil_7_hari
        st.markdown(f"### Rekomendasi Menu Diet Zone — {len(hasil)} Hari")

        HARI_LABEL = ["Senin","Selasa","Rabu","Kamis","Jumat","Sabtu","Minggu"]
        WAKTU_EMOJI = {"B": "Makan Pagi", "L": "Makan Siang", "D": "Makan Malam"}
        WAKTU_HTML  = {
            "B": "waktu-pagi", "L": "waktu-siang", "D": "waktu-malam"
        }

        for hari_idx, kromosom in enumerate(hasil):
            label = HARI_LABEL[hari_idx] if hari_idx < 7 else f"Hari {hari_idx+1}"
            fit   = kromosom.fitness

            with st.expander(
                f"**{label}** — Fitness: `{fit:.4f}`",
                expanded=(hari_idx == 0)
            ):
                waktu_list = [
                    (WaktuMakan.PAGI,  kromosom.pagi,  "B"),
                    (WaktuMakan.SIANG, kromosom.siang, "L"),
                    (WaktuMakan.MALAM, kromosom.malam, "D"),
                ]

                for _, gen_waktu, kode_waktu in waktu_list:
                    gizi    = hitung_rata_gizi(gen_waktu)
                    thr     = THRESHOLD[kode_waktu]
                    d       = math.sqrt(
                        sum((gizi[k]-thr[k])**2 for k in ["karbo","protein","lemak","serat"])
                    )

                    st.markdown(
                        f'<span class="{WAKTU_HTML[kode_waktu]}">'
                        f'{WAKTU_EMOJI[kode_waktu]}</span>'
                        f' &nbsp; Euclidean Distance: **{d:.4f}**',
                        unsafe_allow_html=True
                    )

                    # Tabel makanan
                    rows = []
                    for i, bahan in enumerate(gen_waktu, 1):
                        rows.append({
                            "Gen": f"g{(list('BLD').index(kode_waktu))*3+i}",
                            "Kode": bahan.kode,
                            "Nama Makanan": bahan.nama,
                            "Karbo (g)": f"{bahan.karbohidrat_g:.1f}",
                            "Protein (g)": f"{bahan.protein_g:.1f}",
                            "Lemak (g)": f"{bahan.lemak_g:.1f}",
                            "Serat (g)": f"{bahan.serat_g:.1f}",
                            "% Karbo": f"{bahan.pct_karbohidrat:.1f}%",
                            "% Protein": f"{bahan.pct_protein:.1f}%",
                            "% Lemak": f"{bahan.pct_lemak:.1f}%",
                        })
                    df_menu = pd.DataFrame(rows)
                    st.dataframe(df_menu, use_container_width=True, hide_index=True)

                    # Rata-rata vs threshold
                    cols = st.columns(4)
                    metrics = [
                        ("Karbo",   gizi["karbo"],   thr["karbo"],   "%"),
                        ("Protein", gizi["protein"], thr["protein"], "%"),
                        ("Lemak",   gizi["lemak"],   thr["lemak"],   "%"),
                        ("Serat",   gizi["serat"],   thr["serat"],   " g"),
                    ]
                    for col, (nama, val, thr_val, unit) in zip(cols, metrics):
                        delta = val - thr_val
                        col.metric(
                            f"Avg {nama}",
                            f"{val:.1f}{unit}",
                            f"{delta:+.1f} (target {thr_val:.0f}{unit})",
                            delta_color="off"
                        )
                    st.markdown("---")


# ─────────────────────────────────────────────────────────────────
# TAB 3 — ANALISIS FITNESS
# ─────────────────────────────────────────────────────────────────
with tab3:
    if not st.session_state.history_best:
        st.info("Jalankan Algoritma Genetika terlebih dahulu.")
    else:
        hist_best = st.session_state.history_best
        hist_avg  = st.session_state.history_avg
        hasil     = st.session_state.hasil_7_hari

        st.markdown("### Kurva Konvergensi Fitness")
        df_hist = pd.DataFrame({
            "Fitness Terbaik": hist_best,
            "Fitness Rata-rata": hist_avg,
        })
        st.line_chart(df_hist, height=350)

        st.divider()
        st.markdown("### Fitness per Hari")

        HARI_LABEL = ["Senin","Selasa","Rabu","Kamis","Jumat","Sabtu","Minggu"]
        fitness_data = []
        for i, k in enumerate(hasil):
            label = HARI_LABEL[i] if i < 7 else f"Hari {i+1}"
            gizi_p = hitung_rata_gizi(k.pagi)
            gizi_s = hitung_rata_gizi(k.siang)
            gizi_m = hitung_rata_gizi(k.malam)
            fitness_data.append({
                "Hari": label,
                "Fitness": round(k.fitness, 4),
                "Avg %Karbo Pagi":   round(gizi_p["karbo"], 1),
                "Avg %Protein Pagi": round(gizi_p["protein"], 1),
                "Avg %Lemak Pagi":   round(gizi_p["lemak"], 1),
                "Avg %Karbo Siang":  round(gizi_s["karbo"], 1),
                "Avg %Karbo Malam":  round(gizi_m["karbo"], 1),
            })

        df_fit = pd.DataFrame(fitness_data)
        st.dataframe(df_fit, use_container_width=True, hide_index=True)

        col1, col2, col3 = st.columns(3)
        col1.metric("Fitness Min (Terbaik)", f"{df_fit['Fitness'].min():.4f}")
        col2.metric("Fitness Rata-rata",     f"{df_fit['Fitness'].mean():.4f}")
        col3.metric("Baseline Yuliastuti",   "15.54",
                    delta=f"{df_fit['Fitness'].mean()-15.54:.4f}",
                    delta_color="inverse")


# ─────────────────────────────────────────────────────────────────
# TAB 4 — VERIFIKASI CONSTRAINT
# ─────────────────────────────────────────────────────────────────
with tab4:
    st.markdown("### Verifikasi Hard Constraint Waktu Makan")
    st.markdown("""
    Verifikasi bahwa setiap gen dalam kromosom berasal dari
    subhimpunan waktu makan yang sesuai.
    """)

    if st.session_state.hasil_7_hari is None or st.session_state.kb is None:
        st.info("Jalankan Algoritma Genetika dan hubungkan database terlebih dahulu.")
    else:
        hasil = st.session_state.hasil_7_hari
        kb    = st.session_state.kb

        HARI_LABEL = ["Senin","Selasa","Rabu","Kamis","Jumat","Sabtu","Minggu"]
        semua_valid = True

        for hari_idx, kromosom in enumerate(hasil):
            label   = HARI_LABEL[hari_idx] if hari_idx < 7 else f"Hari {hari_idx+1}"
            laporan = verifikasi_constraint(kromosom, kb)

            if not laporan["semua_valid"]:
                semua_valid = False

            with st.expander(
                f"{label} — {'Semua valid' if laporan['semua_valid'] else 'Ada pelanggaran'}",
                expanded=not laporan["semua_valid"]
            ):
                rows = []
                for d in laporan["detail"]:
                    rows.append({
                        "Gen": d["gen"],
                        "Waktu Makan": d["waktu"],
                        "Nama Makanan": d["nama"],
                        "Status": "Valid" if d["valid"] else "Melanggar constraint",
                    })
                df_v = pd.DataFrame(rows)
                st.dataframe(df_v, use_container_width=True, hide_index=True)

        st.divider()
        if semua_valid:
            st.success("""
             **Semua kromosom valid** — Hard constraint waktu makan terpenuhi 100%.

            Ini membuktikan bahwa Constrained Initialization dan Directed Mutation
            berhasil memastikan setiap gen selalu berasal dari subhimpunan
            waktu makan yang tepat (S_breakfast, S_lunch, S_dinner).
            """)
        else:
            st.error("Ditemukan pelanggaran constraint — periksa implementasi mutasi.")

        st.markdown("""
        #### Penjelasan Mekanisme Constraint

        | Posisi Gen | Waktu Makan | Subhimpunan | Sumber DB |
        |-----------|-------------|-------------|-----------|
        | g1, g2, g3 | Makan Pagi | S_breakfast | v_ag_breakfast |
        | g4, g5, g6 | Makan Siang | S_lunch | v_ag_lunch |
        | g7, g8, g9 | Makan Malam | S_dinner | v_ag_dinner |

        **Constrained Initialization:** Gen hanya dipilih dari pool yang sesuai
        saat pembangkitan populasi awal — constraint terpenuhi sejak generasi pertama.

        **Directed Mutation:** Saat mutasi, pengganti gen diambil dari pool
        waktu makan yang sama dengan posisi gen yang dimutasi —
        constraint dipertahankan di setiap kromosom anak.
        """)


# ════════════════════════════════════════════════════════════════════
# TAB 5 — EVALUASI
# ════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown("## Evaluasi: Pengaruh Knowledge-Based Constraint")
    st.markdown("""
    Evaluasi dilakukan dalam **dua dimensi**:
    - **(a) Matematis** — perbandingan nilai fitness KB-AG vs AG Standar (N run)
    - **(b) Praktis** — validasi relevansi menu dan ketercapaian threshold gizi
    """)
    st.divider()

    if st.session_state.kb is None:
        st.warning("Hubungkan database terlebih dahulu.")
    else:
        kb = st.session_state.kb

        # ── Tombol jalankan evaluasi ──────────────────────────────
        if st.button("▶ Jalankan Evaluasi Komparatif (Standar vs KB-AG)",
                     type="primary", use_container_width=True):

            prog   = st.progress(0)
            status = st.empty()
            total_runs = n_run_eval * 2
            run_counter = [0]

            def cb_eval(fase, run, total, **kw):
                run_counter[0] += 1
                prog.progress(min(run_counter[0]/total_runs, 1.0))
                status.markdown(f"**{fase}** — Run {run}/{total}")

            t0 = time.time()
            hk = evaluasi_komparatif(
                kb=kb, n_run=n_run_eval,
                pop_size=pop_size, n_generasi=n_gen_eval,
                crossover_rate=crossover_rate,
                mutation_rate=mutation_rate,
                n_hari=n_hari, callback=cb_eval
            )
            elapsed = time.time()-t0
            prog.progress(1.0)
            status.success(f"Evaluasi selesai dalam {elapsed:.1f} detik")

            # Ambil satu run kb_ag untuk validasi output
            hasil_kb_single = run_ag(
                kb=kb, mode='kb_ag', pop_size=pop_size,
                n_generasi=n_gen_eval, n_hari=n_hari
            )
            hasil_standar_single = run_ag(
                kb=kb, mode='standar', pop_size=pop_size,
                n_generasi=n_gen_eval, n_hari=n_hari
            )

            vg       = validasi_ketercapaian_gizi(hasil_kb_single.menu_7_hari)
            vg_std   = validasi_ketercapaian_gizi(hasil_standar_single.menu_7_hari)
            vr       = validasi_relevansi_menu(hasil_kb_single.menu_7_hari, kb)
            vr_std   = validasi_relevansi_menu(hasil_standar_single.menu_7_hari, kb)
            bm  = bandingkan_menu(hasil_standar_single.menu_7_hari,
                                  hasil_kb_single.menu_7_hari, kb, n_hari=3)
            rng = rangkuman_evaluasi(hk, vg, vr)

            st.session_state.hasil_komparatif       = hk
            st.session_state.validasi_gizi_kb       = vg
            st.session_state.validasi_gizi_std      = vg_std
            st.session_state.validasi_relevansi_kb  = vr
            st.session_state.validasi_relevansi_std = vr_std
            st.session_state.perbandingan_menu      = bm
            st.session_state.rangkuman              = rng

        # ── Tampilkan hasil jika sudah ada ────────────────────────
        if st.session_state.hasil_komparatif:
            hk   = st.session_state.hasil_komparatif
            vg   = st.session_state.validasi_gizi_kb
            vg_std = st.session_state.validasi_gizi_std
            vr   = st.session_state.validasi_relevansi_kb
            vr_std = st.session_state.validasi_relevansi_std
            bm   = st.session_state.perbandingan_menu
            rng  = st.session_state.rangkuman

            # ── Ringkasan Eksekutif ───────────────────────────────
            st.markdown("---")
            st.markdown("### Ringkasan Eksekutif")
            km = rng["kesimpulan_matematis"]
            kp = rng["kesimpulan_praktis"]

            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Fitness KB-AG",    f"{km['rata_kb']:.4f}",
                      f"{km['selisih_fitness']:+.4f} vs Standar", delta_color="inverse")
            c2.metric("Fitness Standar",  f"{km['rata_standar']:.4f}")
            c3.metric("Baseline (2024)",  "15.54",
                      f"{km['rata_kb']-15.54:+.4f}", delta_color="inverse")
            c4.metric("Constraint Valid", f"{kp['constraint_valid_pct']}%")

            if km["kb_ag_lebih_baik"]:
                st.success(f"KB-AG **lebih baik** secara matematis — peningkatan fitness {km['pct_peningkatan']:.1f}% vs AG Standar")
            else:
                st.info("AG Standar menghasilkan fitness sedikit lebih baik, namun tidak memenuhi constraint waktu makan")

            st.divider()

            # ── Dimensi (a): Evaluasi Komparatif ─────────────────
            st.markdown("### (a) Evaluasi Komparatif — Matematis")

            # Statistik deskriptif
            stat_s = hk["stat_standar"]
            stat_k = hk["stat_kb"]
            df_stat = pd.DataFrame([
                {"Mode":"AG Standar (tanpa constraint)",
                 "Rata-rata Fitness": round(stat_s.rata_rata,4),
                 "Std Deviasi":       round(stat_s.std_deviasi,4),
                 "Terbaik":           round(stat_s.terbaik,4),
                 "Terburuk":          round(stat_s.terburuk,4)},
                {"Mode":"KB-AG (dengan constraint)",
                 "Rata-rata Fitness": round(stat_k.rata_rata,4),
                 "Std Deviasi":       round(stat_k.std_deviasi,4),
                 "Terbaik":           round(stat_k.terbaik,4),
                 "Terburuk":          round(stat_k.terburuk,4)},
                {"Mode":"Baseline Yuliastuti (2024)",
                 "Rata-rata Fitness": 15.54,
                 "Std Deviasi": "-",
                 "Terbaik": 14.0,
                 "Terburuk": "-"},
            ])
            st.markdown(f"**Tabel Statistik Deskriptif** ({stat_s.n_run} run pengujian)")
            st.dataframe(df_stat, hide_index=True, use_container_width=True)

            # Kurva konvergensi rata-rata
            st.markdown("**Kurva Konvergensi Rata-rata** (rata-rata dari semua run)")
            kurva_s = hk["kurva_standar"]
            kurva_k = hk["kurva_kb"]
            min_len = min(len(kurva_s), len(kurva_k))
            if min_len > 0:
                st.line_chart(pd.DataFrame({
                    "AG Standar": kurva_s[:min_len],
                    "KB-AG":      kurva_k[:min_len],
                }), height=320)

            # Distribusi fitness per run
            st.markdown("**Distribusi Fitness per Run**")
            df_run = pd.DataFrame({
                "Run":      list(range(1, stat_s.n_run+1)),
                "AG Standar": [round(f,4) for f in hk["fitness_standar_list"]],
                "KB-AG":      [round(f,4) for f in hk["fitness_kb_list"]],
            })
            st.dataframe(df_run, hide_index=True, use_container_width=True)

            st.divider()

            # ── Dimensi (b): Validasi Praktis ────────────────────
            st.markdown("### (b) Validasi Output — Praktis")

            # ── Ketercapaian Threshold Gizi ──────────────────────
            st.markdown("#### Ketercapaian Threshold Diet Zone per Waktu Makan")

            def hitung_pct_threshold(vg_data):
                total = len(vg_data)
                return {
                    "pct_karbo":   round(sum(1 for r in vg_data if r["memenuhi_karbo"])   / total * 100, 1),
                    "pct_protein": round(sum(1 for r in vg_data if r["memenuhi_protein"]) / total * 100, 1),
                    "pct_lemak":   round(sum(1 for r in vg_data if r["memenuhi_lemak"])   / total * 100, 1),
                }

            pct_kb  = hitung_pct_threshold(vg)
            pct_std = hitung_pct_threshold(vg_std)

            col_kb, col_std = st.columns(2)
            with col_kb:
                st.markdown("**KB-AG**")
                df_gizi_kb = pd.DataFrame(vg)[[
                    "hari","waktu","pct_karbo","pct_protein","pct_lemak","serat_g","euclidean"
                ]]
                df_gizi_kb.columns = ["Hari","Waktu","%Karbo","%Protein","%Lemak","Serat(g)","Euclidean"]
                st.dataframe(df_gizi_kb, hide_index=True, use_container_width=True)

            with col_std:
                st.markdown("**AG Standar**")
                df_gizi_std = pd.DataFrame(vg_std)[[
                    "hari","waktu","pct_karbo","pct_protein","pct_lemak","serat_g","euclidean"
                ]]
                df_gizi_std.columns = ["Hari","Waktu","%Karbo","%Protein","%Lemak","Serat(g)","Euclidean"]
                st.dataframe(df_gizi_std, hide_index=True, use_container_width=True)

            st.markdown("#### Perbandingan Ketercapaian Threshold (±10%)")
            df_thr = pd.DataFrame([
                {
                    "Metrik":                   "Memenuhi threshold karbo (±10%)",
                    "KB-AG":                    f"{pct_kb['pct_karbo']}%",
                    "AG Standar":               f"{pct_std['pct_karbo']}%",
                    "Selisih (KB - Std)":       f"{pct_kb['pct_karbo'] - pct_std['pct_karbo']:+.1f}%",
                },
                {
                    "Metrik":                   "Memenuhi threshold protein (±10%)",
                    "KB-AG":                    f"{pct_kb['pct_protein']}%",
                    "AG Standar":               f"{pct_std['pct_protein']}%",
                    "Selisih (KB - Std)":       f"{pct_kb['pct_protein'] - pct_std['pct_protein']:+.1f}%",
                },
                {
                    "Metrik":                   "Memenuhi threshold lemak (±10%)",
                    "KB-AG":                    f"{pct_kb['pct_lemak']}%",
                    "AG Standar":               f"{pct_std['pct_lemak']}%",
                    "Selisih (KB - Std)":       f"{pct_kb['pct_lemak'] - pct_std['pct_lemak']:+.1f}%",
                },
            ])
            st.dataframe(df_thr, hide_index=True, use_container_width=True)

            st.divider()

            # ── Validasi Relevansi Menu ───────────────────────────
            st.markdown("#### Validasi Relevansi Menu")

            col_r1, col_r2 = st.columns(2)
            with col_r1:
                st.markdown("**KB-AG**")
                st.metric("Constraint waktu makan valid",
                          f"{vr['pct_constraint_valid']}%",
                          f"{vr['valid_gen']}/{vr['total_gen']} gen valid")
                st.metric("Duplikat bahan dalam satu hari",
                          str(vr['duplikat_total']),
                          "tidak ada duplikat" if vr['duplikat_total'] == 0
                          else "item terduplikasi")
                if vr["pct_constraint_valid"] == 100:
                    st.success("Seluruh gen valid untuk waktu makannya")
                else:
                    st.error(f"{100 - vr['pct_constraint_valid']:.1f}% gen melanggar constraint")

            with col_r2:
                st.markdown("**AG Standar**")
                st.metric("Constraint waktu makan valid",
                          f"{vr_std['pct_constraint_valid']}%",
                          f"{vr_std['valid_gen']}/{vr_std['total_gen']} gen valid")
                st.metric("Duplikat bahan dalam satu hari",
                          str(vr_std['duplikat_total']),
                          "tidak ada duplikat" if vr_std['duplikat_total'] == 0
                          else "item terduplikasi")
                if vr_std["pct_constraint_valid"] == 100:
                    st.success("Seluruh gen valid untuk waktu makannya")
                else:
                    st.warning(f"{100 - vr_std['pct_constraint_valid']:.1f}% gen tidak sesuai waktu makan")

            # Tabel ringkasan relevansi berdampingan
            st.markdown("#### Ringkasan Perbandingan Relevansi")
            df_rel = pd.DataFrame([
                {
                    "Metrik":             "Constraint waktu makan valid (%)",
                    "KB-AG":              f"{vr['pct_constraint_valid']}%",
                    "AG Standar":         f"{vr_std['pct_constraint_valid']}%",
                    "Selisih (KB - Std)": f"{vr['pct_constraint_valid'] - vr_std['pct_constraint_valid']:+.1f}%",
                },
                {
                    "Metrik":             "Gen valid (dari total 63 gen / 7 hari)",
                    "KB-AG":              f"{vr['valid_gen']}/{vr['total_gen']}",
                    "AG Standar":         f"{vr_std['valid_gen']}/{vr_std['total_gen']}",
                    "Selisih (KB - Std)": f"{vr['valid_gen'] - vr_std['valid_gen']:+d} gen",
                },
                {
                    "Metrik":             "Duplikat bahan dalam satu hari",
                    "KB-AG":              str(vr['duplikat_total']),
                    "AG Standar":         str(vr_std['duplikat_total']),
                    "Selisih (KB - Std)": f"{vr['duplikat_total'] - vr_std['duplikat_total']:+d}",
                },
            ])
            st.dataframe(df_rel, hide_index=True, use_container_width=True)

            st.divider()

            # ── Perbandingan Menu Konkret ─────────────────────────
            st.markdown("### 🍽️ Perbandingan Menu Konkret (3 Hari Pertama)")
            HARI_L = ["Senin","Selasa","Rabu","Kamis","Jumat","Sabtu","Minggu"]
            for item in bm:
                label = HARI_L[item["hari"]-1]
                st.markdown(f"**{label}**")
                c_s, c_k = st.columns(2)
                with c_s:
                    st.markdown(f"**AG Standar** — Fitness: `{item['standar']['fitness']}`  "
                                f"Constraint Valid: `{item['standar']['pct_valid']}%`")
                    st.markdown(f"*Pagi:* {', '.join(item['standar']['pagi'])}")
                    st.markdown(f"*Siang:* {', '.join(item['standar']['siang'])}")
                    st.markdown(f"*Malam:* {', '.join(item['standar']['malam'])}")
                with c_k:
                    st.markdown(f"**KB-AG** — Fitness: `{item['kb_ag']['fitness']}`  "
                                f"Constraint Valid: `{item['kb_ag']['pct_valid']}%`")
                    st.markdown(f"*Pagi:* {', '.join(item['kb_ag']['pagi'])}")
                    st.markdown(f"*Siang:* {', '.join(item['kb_ag']['siang'])}")
                    st.markdown(f"*Malam:* {', '.join(item['kb_ag']['malam'])}")
                st.markdown("---")

            # ── Kesimpulan ────────────────────────────────────────
            st.markdown("### Kesimpulan Evaluasi")

            kesimpulan_matematis = (
                f"KB-AG menghasilkan rata-rata fitness **{km['rata_kb']:.4f}** "
                f"({'lebih baik' if km['kb_ag_lebih_baik'] else 'lebih buruk'} "
                f"dibanding AG Standar {km['rata_standar']:.4f}, "
                f"selisih {abs(km['selisih_fitness']):.4f}). "
                f"{'KB-AG juga lebih baik' if km['kb_ag_vs_baseline'] else 'KB-AG belum melampaui'} "
                f"dari baseline Yuliastuti et al. (2024) sebesar 15,54."
            )
            kesimpulan_praktis = (
                f"Seluruh gen KB-AG valid terhadap constraint waktu makan "
                f"({kp['constraint_valid_pct']}%), "
                f"sedangkan AG Standar tidak menjamin hal ini. "
                f"Threshold karbo terpenuhi pada {kp['pct_memenuhi_karbo']}% waktu makan, "
                f"protein pada {kp['pct_memenuhi_protein']}%, "
                f"dan lemak pada {kp['pct_memenuhi_lemak']}%."
            )

            st.info(
                f"**Matematis:** KB-AG menghasilkan rata-rata fitness "
                f"**{km['rata_kb']:.4f}** "
                f"({'lebih baik' if km['kb_ag_lebih_baik'] else 'lebih buruk'} "
                f"dibanding AG Standar {km['rata_standar']:.4f}, "
                f"selisih {abs(km['selisih_fitness']):.4f}). "
                f"{'KB-AG juga lebih baik' if km['kb_ag_vs_baseline'] else 'KB-AG belum melampaui'} "
                f"dari baseline Yuliastuti et al. (2024) sebesar 15,54."
            )
            st.info(
                f"**Praktis:** KB-AG memiliki constraint valid {kp['constraint_valid_pct']}% "
                f"vs AG Standar {vr_std['pct_constraint_valid']}%. "
                f"Threshold karbo: KB-AG {pct_kb['pct_karbo']}% vs Standar {pct_std['pct_karbo']}%. "
                f"Threshold protein: KB-AG {pct_kb['pct_protein']}% vs Standar {pct_std['pct_protein']}%. "
                f"Threshold lemak: KB-AG {pct_kb['pct_lemak']}% vs Standar {pct_std['pct_lemak']}%."
            )
