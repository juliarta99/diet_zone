"""
evaluasi.py
───────────
Modul Evaluasi untuk Rumusan Masalah 3:
Membandingkan kualitas solusi AG Standar vs KB-AG (Knowledge-Based)

Dimensi (a) — Evaluasi Komparatif (Matematis):
  - AG Standar: gen dibangkitkan acak dari seluruh pool tanpa batasan
  - KB-AG: Constrained Initialization + Directed Mutation (RM 2)
  - Metrik: rata-rata fitness, std deviasi, fitness terbaik, konvergensi

Dimensi (b) — Validasi Output (Praktis):
  - Verifikasi constraint waktu makan
  - Relevansi menu (tidak ada makanan tidak sesuai waktu)
  - Ketercapaian threshold gizi Diet Zone
  - Perbandingan contoh menu konkret
"""

import random
import math
import copy
import statistics
from dataclasses import dataclass, field
from typing import List, Dict, Tuple

from genetic_algorithm import (
    KnowledgeBase, Kromosom, BahanPangan,
    WaktuMakan, GEN_WAKTU_MAP,
    constrained_initialization, directed_mutation,
    two_point_crossover, seleksi_rank_based,
    hitung_fitness, hitung_rata_gizi,
    euclidean_distance, THRESHOLD,
    verifikasi_constraint
)


# ═══════════════════════════════════════════════════════════════════
# AG STANDAR — TANPA CONSTRAINT (baseline Yuliastuti et al., 2024)
# ═══════════════════════════════════════════════════════════════════

def standar_initialization(kb: KnowledgeBase) -> Kromosom:
    """
    Inisialisasi STANDAR: gen dipilih acak dari GABUNGAN seluruh pool
    tanpa mempertimbangkan waktu makan — menyimulasikan pendekatan
    Yuliastuti et al. (2024) yang menggunakan 340 data tanpa batasan.
    """
    # Gabung seluruh pool menjadi satu himpunan
    semua_bahan = (
        kb.get_pool(WaktuMakan.PAGI) +
        kb.get_pool(WaktuMakan.SIANG) +
        kb.get_pool(WaktuMakan.MALAM)
    )
    # Deduplikasi berdasarkan ID
    seen = set()
    pool_gabungan = []
    for b in semua_bahan:
        if b.id not in seen:
            seen.add(b.id)
            pool_gabungan.append(b)

    gen = [random.choice(pool_gabungan) for _ in range(9)]
    kromosom = Kromosom(gen=gen)
    kromosom.fitness = hitung_fitness(kromosom)
    return kromosom


def standar_mutation(kromosom: Kromosom, kb: KnowledgeBase,
                     mutation_rate: float = 0.1) -> Kromosom:
    """
    Mutasi STANDAR: pengganti gen diambil dari seluruh database
    tanpa mempertimbangkan posisi/waktu makan.
    """
    semua_bahan = (
        kb.get_pool(WaktuMakan.PAGI) +
        kb.get_pool(WaktuMakan.SIANG) +
        kb.get_pool(WaktuMakan.MALAM)
    )
    seen = set()
    pool_gabungan = []
    for b in semua_bahan:
        if b.id not in seen:
            seen.add(b.id)
            pool_gabungan.append(b)

    gen_baru = copy.copy(kromosom.gen)
    for posisi in range(Kromosom.N_GEN):
        if random.random() < mutation_rate:
            gen_baru[posisi] = random.choice(pool_gabungan)

    child = Kromosom(gen=gen_baru)
    child.fitness = hitung_fitness(child)
    return child


# ═══════════════════════════════════════════════════════════════════
# RUNNER AG — GENERIK UNTUK STANDAR DAN KB
# ═══════════════════════════════════════════════════════════════════

@dataclass
class HasilEksperimen:
    """Hasil satu kali eksperimen AG (satu run)."""
    mode: str               # 'standar' atau 'kb_ag'
    run_ke: int
    fitness_per_generasi: List[float] = field(default_factory=list)
    avg_per_generasi:     List[float] = field(default_factory=list)
    fitness_akhir:        float = 0.0
    menu_7_hari:          List[Kromosom] = field(default_factory=list)


def run_ag(
    kb: KnowledgeBase,
    mode: str,              # 'standar' atau 'kb_ag'
    pop_size: int = 70,
    n_generasi: int = 800,
    crossover_rate: float = 0.8,
    mutation_rate: float = 0.1,
    n_hari: int = 7,
    run_ke: int = 1,
    callback=None
) -> HasilEksperimen:
    """
    Jalankan AG satu kali dengan mode tertentu.
    mode='standar' → AG tanpa constraint (baseline)
    mode='kb_ag'   → AG dengan Constrained Initialization + Directed Mutation
    """
    hasil = HasilEksperimen(mode=mode, run_ke=run_ke)
    semua_best = []
    semua_avg  = []
    menu_7_hari = []

    for hari in range(n_hari):
        # Inisialisasi populasi
        if mode == 'kb_ag':
            populasi = [constrained_initialization(kb) for _ in range(pop_size)]
        else:
            populasi = [standar_initialization(kb) for _ in range(pop_size)]

        hist_best = []
        hist_avg  = []

        for gen_idx in range(n_generasi):
            offspring = list(populasi)

            # Crossover
            random.shuffle(populasi)
            for i in range(0, len(populasi) - 1, 2):
                if random.random() < crossover_rate:
                    c1, c2 = two_point_crossover(populasi[i], populasi[i+1])
                    offspring.extend([c1, c2])

            # Mutasi
            for kromo in populasi:
                if mode == 'kb_ag':
                    mutant = directed_mutation(kromo, kb, mutation_rate)
                else:
                    mutant = standar_mutation(kromo, kb, mutation_rate)
                offspring.append(mutant)

            # Seleksi
            populasi = seleksi_rank_based(offspring, pop_size)

            best = populasi[0].fitness
            avg  = sum(k.fitness for k in populasi) / len(populasi)
            hist_best.append(best)
            hist_avg.append(avg)

            if callback:
                callback(mode=mode, run_ke=run_ke, hari=hari+1,
                         generasi=gen_idx+1, best=best, avg=avg)

        semua_best.extend(hist_best)
        semua_avg.extend(hist_avg)
        menu_7_hari.append(populasi[0])

    hasil.fitness_per_generasi = semua_best
    hasil.avg_per_generasi     = semua_avg
    hasil.fitness_akhir        = sum(k.fitness for k in menu_7_hari) / len(menu_7_hari)
    hasil.menu_7_hari          = menu_7_hari
    return hasil


# ═══════════════════════════════════════════════════════════════════
# EVALUASI KOMPARATIF — DIMENSI (a)
# ═══════════════════════════════════════════════════════════════════

@dataclass
class RingkasanStatistik:
    """Statistik dari N kali pengujian satu mode AG."""
    mode: str
    n_run: int
    fitness_list: List[float]
    rata_rata:    float = 0.0
    std_deviasi:  float = 0.0
    terbaik:      float = 0.0
    terburuk:     float = 0.0

    def __post_init__(self):
        if self.fitness_list:
            self.rata_rata   = statistics.mean(self.fitness_list)
            self.std_deviasi = statistics.stdev(self.fitness_list) if len(self.fitness_list) > 1 else 0.0
            self.terbaik     = min(self.fitness_list)
            self.terburuk    = max(self.fitness_list)


def evaluasi_komparatif(
    kb: KnowledgeBase,
    n_run: int = 10,
    pop_size: int = 70,
    n_generasi: int = 800,
    crossover_rate: float = 0.8,
    mutation_rate: float = 0.1,
    n_hari: int = 7,
    callback=None
) -> Dict:
    """
    Jalankan N kali eksperimen untuk kedua mode AG.
    Kembalikan statistik komparatif lengkap.
    """
    hasil_standar = []
    hasil_kb      = []
    konvergensi_standar = []
    konvergensi_kb      = []

    total_steps = n_run * 2  # standar + kb

    for run in range(1, n_run + 1):
        if callback:
            callback(fase="Standar AG", run=run, total=n_run)

        eks_standar = run_ag(
            kb=kb, mode='standar',
            pop_size=pop_size, n_generasi=n_generasi,
            crossover_rate=crossover_rate, mutation_rate=mutation_rate,
            n_hari=n_hari, run_ke=run
        )
        hasil_standar.append(eks_standar.fitness_akhir)
        konvergensi_standar.append(eks_standar.fitness_per_generasi[:n_generasi])

        if callback:
            callback(fase="KB-AG", run=run, total=n_run)

        eks_kb = run_ag(
            kb=kb, mode='kb_ag',
            pop_size=pop_size, n_generasi=n_generasi,
            crossover_rate=crossover_rate, mutation_rate=mutation_rate,
            n_hari=n_hari, run_ke=run
        )
        hasil_kb.append(eks_kb.fitness_akhir)
        konvergensi_kb.append(eks_kb.fitness_per_generasi[:n_generasi])

    stat_standar = RingkasanStatistik(
        mode='AG Standar', n_run=n_run, fitness_list=hasil_standar
    )
    stat_kb = RingkasanStatistik(
        mode='KB-AG', n_run=n_run, fitness_list=hasil_kb
    )

    # Rata-rata kurva konvergensi per generasi
    def avg_kurva(list_of_lists):
        if not list_of_lists: return []
        min_len = min(len(l) for l in list_of_lists)
        return [
            sum(l[i] for l in list_of_lists) / len(list_of_lists)
            for i in range(min_len)
        ]

    return {
        "stat_standar":        stat_standar,
        "stat_kb":             stat_kb,
        "kurva_standar":       avg_kurva(konvergensi_standar),
        "kurva_kb":            avg_kurva(konvergensi_kb),
        "fitness_standar_list": hasil_standar,
        "fitness_kb_list":     hasil_kb,
        "baseline_yuliastuti": 15.54,
    }


# ═══════════════════════════════════════════════════════════════════
# VALIDASI OUTPUT — DIMENSI (b)
# ═══════════════════════════════════════════════════════════════════

def validasi_ketercapaian_gizi(menu_7_hari: List[Kromosom]) -> List[Dict]:
    """
    Periksa seberapa dekat setiap waktu makan dengan threshold Diet Zone.
    Kembalikan laporan deviasi per hari per waktu makan.
    """
    laporan = []
    for hari_idx, kromosom in enumerate(menu_7_hari):
        for waktu_label, gen_waktu, kode_waktu in [
            ("Pagi",  kromosom.pagi,  WaktuMakan.PAGI),
            ("Siang", kromosom.siang, WaktuMakan.SIANG),
            ("Malam", kromosom.malam, WaktuMakan.MALAM),
        ]:
            gizi = hitung_rata_gizi(gen_waktu)
            thr  = THRESHOLD[kode_waktu]
            deviasi_karbo   = abs(gizi["karbo"]   - thr["karbo"])
            deviasi_protein = abs(gizi["protein"] - thr["protein"])
            deviasi_lemak   = abs(gizi["lemak"]   - thr["lemak"])
            deviasi_serat   = abs(gizi["serat"]   - thr["serat"])
            eucl = euclidean_distance(gizi, thr)

            laporan.append({
                "hari":            hari_idx + 1,
                "waktu":           waktu_label,
                "pct_karbo":       round(gizi["karbo"],   2),
                "pct_protein":     round(gizi["protein"], 2),
                "pct_lemak":       round(gizi["lemak"],   2),
                "serat_g":         round(gizi["serat"],   2),
                "dev_karbo":       round(deviasi_karbo,   2),
                "dev_protein":     round(deviasi_protein, 2),
                "dev_lemak":       round(deviasi_lemak,   2),
                "dev_serat":       round(deviasi_serat,   2),
                "euclidean":       round(eucl, 4),
                "memenuhi_karbo":  deviasi_karbo   <= 10,
                "memenuhi_protein":deviasi_protein <= 10,
                "memenuhi_lemak":  deviasi_lemak   <= 10,
                "memenuhi_serat":  gizi["serat"]   >= 5,
            })
    return laporan


def validasi_relevansi_menu(
    menu_7_hari: List[Kromosom],
    kb: KnowledgeBase
) -> Dict:
    """
    Periksa relevansi menu secara praktis:
    1. Constraint waktu makan (100% harus valid)
    2. Keragaman bahan (tidak ada bahan yang sama dalam satu hari)
    3. Distribusi kelompok makanan
    """
    total_gen       = 0
    valid_gen       = 0
    duplikat_dalam_hari = 0
    kelompok_count  = {}

    detail_per_hari = []

    for hari_idx, kromosom in enumerate(menu_7_hari):
        verif = verifikasi_constraint(kromosom, kb)
        valid_gen += sum(1 for d in verif["detail"] if d["valid"])
        total_gen += len(verif["detail"])

        # Cek duplikat dalam satu hari
        nama_list = [g.nama for g in kromosom.gen]
        duplikat  = len(nama_list) - len(set(nama_list))
        duplikat_dalam_hari += duplikat

        # Distribusi kelompok
        for g in kromosom.gen:
            kelompok_count[g.kelompok_id] = kelompok_count.get(g.kelompok_id, 0) + 1

        detail_per_hari.append({
            "hari":          hari_idx + 1,
            "constraint_ok": verif["semua_valid"],
            "duplikat":      duplikat,
            "menu_pagi":     [g.nama for g in kromosom.pagi],
            "menu_siang":    [g.nama for g in kromosom.siang],
            "menu_malam":    [g.nama for g in kromosom.malam],
            "fitness":       round(kromosom.fitness, 4),
        })

    pct_constraint_valid = (valid_gen / total_gen * 100) if total_gen > 0 else 0

    return {
        "total_gen":             total_gen,
        "valid_gen":             valid_gen,
        "pct_constraint_valid":  round(pct_constraint_valid, 2),
        "duplikat_total":        duplikat_dalam_hari,
        "kelompok_distribusi":   kelompok_count,
        "detail_per_hari":       detail_per_hari,
    }


def bandingkan_menu(
    menu_standar: List[Kromosom],
    menu_kb: List[Kromosom],
    kb: KnowledgeBase,
    n_hari: int = 3
) -> List[Dict]:
    """
    Bandingkan menu AG Standar vs KB-AG secara berdampingan
    untuk n_hari hari pertama.
    """
    perbandingan = []
    for i in range(min(n_hari, len(menu_standar), len(menu_kb))):
        verif_standar = verifikasi_constraint(menu_standar[i], kb)
        verif_kb      = verifikasi_constraint(menu_kb[i],      kb)

        pct_valid_standar = sum(1 for d in verif_standar["detail"] if d["valid"]) / 9 * 100
        pct_valid_kb      = sum(1 for d in verif_kb["detail"]      if d["valid"]) / 9 * 100

        perbandingan.append({
            "hari": i + 1,
            "standar": {
                "fitness":      round(menu_standar[i].fitness, 4),
                "pagi":         [g.nama for g in menu_standar[i].pagi],
                "siang":        [g.nama for g in menu_standar[i].siang],
                "malam":        [g.nama for g in menu_standar[i].malam],
                "pct_valid":    round(pct_valid_standar, 1),
            },
            "kb_ag": {
                "fitness":      round(menu_kb[i].fitness, 4),
                "pagi":         [g.nama for g in menu_kb[i].pagi],
                "siang":        [g.nama for g in menu_kb[i].siang],
                "malam":        [g.nama for g in menu_kb[i].malam],
                "pct_valid":    round(pct_valid_kb, 1),
            },
        })

    return perbandingan


def rangkuman_evaluasi(hasil_komparatif: Dict, validasi_gizi: List[Dict],
                       validasi_relevansi: Dict) -> Dict:
    """
    Buat rangkuman eksekutif evaluasi RM 3.
    """
    stat_s = hasil_komparatif["stat_standar"]
    stat_k = hasil_komparatif["stat_kb"]
    baseline = hasil_komparatif["baseline_yuliastuti"]

    selisih_rata     = stat_s.rata_rata - stat_k.rata_rata
    pct_peningkatan  = (selisih_rata / stat_s.rata_rata * 100) if stat_s.rata_rata > 0 else 0

    memenuhi_karbo   = sum(1 for r in validasi_gizi if r["memenuhi_karbo"])
    memenuhi_protein = sum(1 for r in validasi_gizi if r["memenuhi_protein"])
    memenuhi_lemak   = sum(1 for r in validasi_gizi if r["memenuhi_lemak"])
    total_waktu      = len(validasi_gizi)

    return {
        "kesimpulan_matematis": {
            "kb_ag_lebih_baik":     stat_k.rata_rata < stat_s.rata_rata,
            "kb_ag_vs_baseline":    stat_k.rata_rata < baseline,
            "selisih_fitness":      round(selisih_rata, 4),
            "pct_peningkatan":      round(pct_peningkatan, 2),
            "rata_standar":         round(stat_s.rata_rata, 4),
            "rata_kb":              round(stat_k.rata_rata, 4),
            "std_standar":          round(stat_s.std_deviasi, 4),
            "std_kb":               round(stat_k.std_deviasi, 4),
        },
        "kesimpulan_praktis": {
            "constraint_valid_pct": validasi_relevansi["pct_constraint_valid"],
            "pct_memenuhi_karbo":   round(memenuhi_karbo / total_waktu * 100, 1),
            "pct_memenuhi_protein": round(memenuhi_protein / total_waktu * 100, 1),
            "pct_memenuhi_lemak":   round(memenuhi_lemak / total_waktu * 100, 1),
        },
    }