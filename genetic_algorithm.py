"""
genetic_algorithm.py
────────────────────
Modul inti Algoritma Genetika dengan Knowledge-Based Constraint
untuk optimasi menu Diet Zone 7 hari.

Menjawab Rumusan Masalah 2:
  (a) Constrained Initialization — gen g1-g3 HANYA dari S_breakfast,
      g4-g6 dari S_lunch, g7-g9 dari S_dinner
  (b) Directed Mutation — gen posisi ke-i hanya diganti dari
      subhimpunan waktu makan yang sama

Referensi: Yuliastuti et al. (2024), TEKNIKA 13(1):18-26
"""

import random
import math
import copy
from dataclasses import dataclass, field
from typing import List, Dict, Tuple

# ═══════════════════════════════════════════════════════════════════
# STRUKTUR DATA
# ═══════════════════════════════════════════════════════════════════

@dataclass
class BahanPangan:
    """Representasi satu bahan pangan dari knowledge base."""
    id: int
    kode: str
    nama: str
    kelompok_id: int
    karbohidrat_g: float
    protein_g: float
    lemak_g: float
    serat_g: float
    pct_karbohidrat: float
    pct_protein: float
    pct_lemak: float


@dataclass
class WaktuMakan:
    PAGI  = "B"   # Breakfast : gen g1, g2, g3
    SIANG = "L"   # Lunch     : gen g4, g5, g6
    MALAM = "D"   # Dinner    : gen g7, g8, g9


# Urutan posisi gen dalam kromosom (9 gen per hari)
# [g1,g2,g3] = pagi | [g4,g5,g6] = siang | [g7,g8,g9] = malam
GEN_WAKTU_MAP = {
    0: WaktuMakan.PAGI,  1: WaktuMakan.PAGI,  2: WaktuMakan.PAGI,
    3: WaktuMakan.SIANG, 4: WaktuMakan.SIANG, 5: WaktuMakan.SIANG,
    6: WaktuMakan.MALAM, 7: WaktuMakan.MALAM, 8: WaktuMakan.MALAM,
}

# Threshold Diet Zone (Yuliastuti et al., 2024; Sears, 2000)
THRESHOLD = {
    WaktuMakan.PAGI:  {"karbo": 40.0, "protein": 30.0, "lemak": 30.0, "serat": 8.33},
    WaktuMakan.SIANG: {"karbo": 40.0, "protein": 30.0, "lemak": 30.0, "serat": 8.33},
    WaktuMakan.MALAM: {"karbo": 40.0, "protein": 30.0, "lemak": 30.0, "serat": 8.33},
}


# ═══════════════════════════════════════════════════════════════════
# KNOWLEDGE BASE — CONSTRAINED SEARCH SPACE
# ═══════════════════════════════════════════════════════════════════

class KnowledgeBase:
    """
    Menyimpan subhimpunan bahan pangan per waktu makan.
    S_breakfast, S_lunch, S_dinner diambil dari database MySQL
    melalui view v_ag_breakfast, v_ag_lunch, v_ag_dinner.
    """

    def __init__(self):
        self.pool: Dict[str, List[BahanPangan]] = {
            WaktuMakan.PAGI:  [],
            WaktuMakan.SIANG: [],
            WaktuMakan.MALAM: [],
        }

    def load_from_db(self, conn):
        """
        Ambil pool bahan pangan dari view database.
        View sudah memfilter berdasarkan tabel bahan_waktu_makan (hard constraint).
        """
        import mysql.connector
        cursor = conn.cursor(dictionary=True)

        view_map = {
            WaktuMakan.PAGI:  "v_ag_breakfast",
            WaktuMakan.SIANG: "v_ag_lunch",
            WaktuMakan.MALAM: "v_ag_dinner",
        }

        for waktu, view_name in view_map.items():
            cursor.execute(f"""
                SELECT id, kode, nama, kelompok_id,
                       COALESCE(karbohidrat_g, 0) AS karbohidrat_g,
                       COALESCE(protein_g, 0)     AS protein_g,
                       COALESCE(lemak_g, 0)        AS lemak_g,
                       COALESCE(serat_g, 0)        AS serat_g,
                       COALESCE(pct_karbohidrat, 0) AS pct_karbohidrat,
                       COALESCE(pct_protein, 0)    AS pct_protein,
                       COALESCE(pct_lemak, 0)      AS pct_lemak
                FROM `{view_name}`
            """)
            rows = cursor.fetchall()
            self.pool[waktu] = [BahanPangan(**row) for row in rows]

        cursor.close()

    def load_from_dataframes(self, df_breakfast, df_lunch, df_dinner):
        """
        Load dari DataFrame pandas (fallback jika tidak ada koneksi DB).
        Digunakan untuk testing dan demo.
        """
        def df_to_pool(df):
            items = []
            for _, row in df.iterrows():
                items.append(BahanPangan(
                    id=int(row['id']),
                    kode=str(row['kode']),
                    nama=str(row['nama']),
                    kelompok_id=int(row.get('kelompok_id', 0)),
                    karbohidrat_g=float(row.get('karbohidrat_g', 0) or 0),
                    protein_g=float(row.get('protein_g', 0) or 0),
                    lemak_g=float(row.get('lemak_g', 0) or 0),
                    serat_g=float(row.get('serat_g', 0) or 0),
                    pct_karbohidrat=float(row.get('pct_karbohidrat', 0) or 0),
                    pct_protein=float(row.get('pct_protein', 0) or 0),
                    pct_lemak=float(row.get('pct_lemak', 0) or 0),
                ))
            return items

        self.pool[WaktuMakan.PAGI]  = df_to_pool(df_breakfast)
        self.pool[WaktuMakan.SIANG] = df_to_pool(df_lunch)
        self.pool[WaktuMakan.MALAM] = df_to_pool(df_dinner)

    def get_pool(self, waktu: str) -> List[BahanPangan]:
        return self.pool[waktu]

    def random_item(self, waktu: str) -> BahanPangan:
        """Pilih satu item acak dari pool waktu makan tertentu."""
        return random.choice(self.pool[waktu])

    def info(self) -> Dict:
        return {
            "S_breakfast": len(self.pool[WaktuMakan.PAGI]),
            "S_lunch":     len(self.pool[WaktuMakan.SIANG]),
            "S_dinner":    len(self.pool[WaktuMakan.MALAM]),
        }


# ═══════════════════════════════════════════════════════════════════
# KROMOSOM
# ═══════════════════════════════════════════════════════════════════

class Kromosom:
    """
    Kromosom merepresentasikan menu makan 1 hari.
    Struktur: 9 gen = [g1,g2,g3 | g4,g5,g6 | g7,g8,g9]
              Pagi         Siang         Malam

    Sesuai Gambar 1 & 2, Yuliastuti et al. (2024).
    """

    N_GEN = 9  # 3 waktu makan × 3 jenis makanan

    def __init__(self, gen: List[BahanPangan] = None):
        self.gen: List[BahanPangan] = gen or []
        self.fitness: float = float('inf')  # semakin kecil semakin baik

    # ── Aksesor per waktu makan ────────────────────────────────────
    @property
    def pagi(self) -> List[BahanPangan]:
        return self.gen[0:3]   # g1, g2, g3

    @property
    def siang(self) -> List[BahanPangan]:
        return self.gen[3:6]   # g4, g5, g6

    @property
    def malam(self) -> List[BahanPangan]:
        return self.gen[6:9]   # g7, g8, g9

    def get_waktu(self, waktu: str) -> List[BahanPangan]:
        if waktu == WaktuMakan.PAGI:  return self.pagi
        if waktu == WaktuMakan.SIANG: return self.siang
        return self.malam

    def __repr__(self):
        return (f"Kromosom(fitness={self.fitness:.4f}, "
                f"pagi={[g.nama[:15] for g in self.pagi]}, "
                f"siang={[g.nama[:15] for g in self.siang]}, "
                f"malam={[g.nama[:15] for g in self.malam]})")


# ═══════════════════════════════════════════════════════════════════
# FUNGSI FITNESS — EUCLIDEAN DISTANCE
# ═══════════════════════════════════════════════════════════════════

def hitung_rata_gizi(gen_waktu: List[BahanPangan]) -> Dict:
    """
    Preprocessing: hitung rata-rata % makronutrien dan serat
    dari 3 makanan dalam satu waktu makan.
    Sesuai preprocessing langkah 2 & 3, Yuliastuti et al. (2024).
    """
    n = len(gen_waktu)
    if n == 0:
        return {"karbo": 0, "protein": 0, "lemak": 0, "serat": 0}

    avg_karbo   = sum(g.pct_karbohidrat for g in gen_waktu) / n
    avg_protein = sum(g.pct_protein     for g in gen_waktu) / n
    avg_lemak   = sum(g.pct_lemak       for g in gen_waktu) / n
    avg_serat   = sum(g.serat_g         for g in gen_waktu) / n

    return {
        "karbo":   avg_karbo,
        "protein": avg_protein,
        "lemak":   avg_lemak,
        "serat":   avg_serat,
    }


def euclidean_distance(gizi: Dict, threshold: Dict) -> float:
    """
    Euclidean Distance antara nilai gizi aktual dengan threshold.
    Persamaan 1 & 2, Yuliastuti et al. (2024):
      d = sqrt((Xk - Tk)² + (Xp - Tp)² + (Xl - Tl)² + (Xs - Ts)²)
    """
    return math.sqrt(
        (gizi["karbo"]   - threshold["karbo"])   ** 2 +
        (gizi["protein"] - threshold["protein"]) ** 2 +
        (gizi["lemak"]   - threshold["lemak"])   ** 2 +
        (gizi["serat"]   - threshold["serat"])   ** 2
    )


def hitung_fitness(kromosom: Kromosom) -> float:
    """
    Fitness total kromosom = jumlah Euclidean Distance 3 waktu makan.
    Nilai terkecil = kromosom terbaik.
    """
    d_pagi  = euclidean_distance(
        hitung_rata_gizi(kromosom.pagi),
        THRESHOLD[WaktuMakan.PAGI]
    )
    d_siang = euclidean_distance(
        hitung_rata_gizi(kromosom.siang),
        THRESHOLD[WaktuMakan.SIANG]
    )
    d_malam = euclidean_distance(
        hitung_rata_gizi(kromosom.malam),
        THRESHOLD[WaktuMakan.MALAM]
    )
    return d_pagi + d_siang + d_malam


# ═══════════════════════════════════════════════════════════════════
# (a) CONSTRAINED INITIALIZATION — RUMUSAN MASALAH 2a
# ═══════════════════════════════════════════════════════════════════

def constrained_initialization(kb: KnowledgeBase) -> Kromosom:
    """
    Bangkitkan satu kromosom dengan hard constraint waktu makan.

    PERBEDAAN dengan Yuliastuti et al. (2024):
      - Yuliastuti: gen dipilih acak dari SELURUH 340 data (tanpa batasan)
      - Penelitian ini: gen dipilih HANYA dari subhimpunan waktu makan:
          g1,g2,g3 ∈ S_breakfast (749 item)
          g4,g5,g6 ∈ S_lunch     (1.040 item)
          g7,g8,g9 ∈ S_dinner    (868 item)

    Dengan demikian setiap kromosom yang dibangkitkan sudah memenuhi
    hard constraint waktu makan sejak awal — tidak perlu validasi ulang.
    """
    gen = []

    # g1, g2, g3 — HANYA dari S_breakfast
    for _ in range(3):
        gen.append(kb.random_item(WaktuMakan.PAGI))

    # g4, g5, g6 — HANYA dari S_lunch
    for _ in range(3):
        gen.append(kb.random_item(WaktuMakan.SIANG))

    # g7, g8, g9 — HANYA dari S_dinner
    for _ in range(3):
        gen.append(kb.random_item(WaktuMakan.MALAM))

    kromosom = Kromosom(gen=gen)
    kromosom.fitness = hitung_fitness(kromosom)
    return kromosom


def init_populasi(kb: KnowledgeBase, pop_size: int) -> List[Kromosom]:
    """
    Bangkitkan populasi awal sejumlah pop_size kromosom,
    semua menggunakan Constrained Initialization.
    """
    return [constrained_initialization(kb) for _ in range(pop_size)]


# ═══════════════════════════════════════════════════════════════════
# CROSSOVER — TWO POINT CROSSOVER
# ═══════════════════════════════════════════════════════════════════

def two_point_crossover(
    parent1: Kromosom,
    parent2: Kromosom
) -> Tuple[Kromosom, Kromosom]:
    """
    Two Point Crossover sesuai Yuliastuti et al. (2024), Gambar 3.
    Tukar segmen gen antara dua parent untuk menghasilkan dua child.

    Crossover TIDAK melanggar constraint karena:
    - Parent1 dan Parent2 sudah valid (dari constrained init)
    - Posisi gen tidak berubah — gen posisi pagi tetap pagi,
      siang tetap siang, malam tetap malam
    - Yang ditukar adalah NILAI gen, bukan POSISI gen
    """
    n = Kromosom.N_GEN
    # Pilih dua titik potong secara acak
    pt1, pt2 = sorted(random.sample(range(1, n), 2))

    gen1 = (parent1.gen[:pt1] +
            parent2.gen[pt1:pt2] +
            parent1.gen[pt2:])

    gen2 = (parent2.gen[:pt1] +
            parent1.gen[pt1:pt2] +
            parent2.gen[pt2:])

    child1 = Kromosom(gen=gen1)
    child2 = Kromosom(gen=gen2)
    child1.fitness = hitung_fitness(child1)
    child2.fitness = hitung_fitness(child2)

    return child1, child2


# ═══════════════════════════════════════════════════════════════════
# (b) DIRECTED MUTATION — RUMUSAN MASALAH 2b
# ═══════════════════════════════════════════════════════════════════

def directed_mutation(
    kromosom: Kromosom,
    kb: KnowledgeBase,
    mutation_rate: float = 0.1
) -> Kromosom:
    """
    Directed Mutation: gen yang dimutasi HANYA diganti dari subhimpunan
    waktu makan yang SAMA dengan posisi gen tersebut.

    PERBEDAAN dengan Yuliastuti et al. (2024):
      - Yuliastuti: nilai pengganti diambil acak dari SELURUH database
        → bisa melanggar constraint (gen posisi pagi terisi makanan malam)
      - Penelitian ini: nilai pengganti diambil dari subhimpunan
        yang SAMA dengan posisi gen:
          posisi 0,1,2 → pengganti dari S_breakfast
          posisi 3,4,5 → pengganti dari S_lunch
          posisi 6,7,8 → pengganti dari S_dinner

    Teknik: Random Injection (Yuliastuti et al., 2024)
    Setiap gen dipilih untuk mutasi berdasarkan mutation_rate.
    """
    gen_baru = copy.copy(kromosom.gen)

    for posisi in range(Kromosom.N_GEN):
        if random.random() < mutation_rate:
            # Tentukan waktu makan berdasarkan POSISI gen
            waktu = GEN_WAKTU_MAP[posisi]
            # Pengganti HANYA dari subhimpunan waktu makan yang sama
            gen_baru[posisi] = kb.random_item(waktu)

    child = Kromosom(gen=gen_baru)
    child.fitness = hitung_fitness(child)
    return child


# ═══════════════════════════════════════════════════════════════════
# SELEKSI — RANK BASED FITNESS
# ═══════════════════════════════════════════════════════════════════

def seleksi_rank_based(
    offspring: List[Kromosom],
    pop_size: int
) -> List[Kromosom]:
    """
    Rank Based Fitness Selection sesuai Yuliastuti et al. (2024).
    Urutkan offspring dari fitness terkecil (terbaik) ke terbesar,
    pertahankan pop_size terbaik untuk generasi berikutnya.
    """
    offspring_sorted = sorted(offspring, key=lambda k: k.fitness)
    return offspring_sorted[:pop_size]


# ═══════════════════════════════════════════════════════════════════
# ALGORITMA GENETIKA UTAMA
# ═══════════════════════════════════════════════════════════════════

class AlgoritmaGenetika:
    """
    Algoritma Genetika dengan Knowledge-Based Constraint.
    Mengintegrasikan Constrained Initialization (RM 2a)
    dan Directed Mutation (RM 2b).
    """

    def __init__(
        self,
        kb: KnowledgeBase,
        pop_size: int = 70,
        n_generasi: int = 800,
        crossover_rate: float = 0.8,
        mutation_rate: float = 0.1,
        n_hari: int = 7,
    ):
        self.kb             = kb
        self.pop_size       = pop_size
        self.n_generasi     = n_generasi
        self.crossover_rate = crossover_rate
        self.mutation_rate  = mutation_rate
        self.n_hari         = n_hari

        # Log untuk visualisasi konvergensi
        self.history_fitness: List[float] = []
        self.history_best:    List[float] = []
        self.populasi:        List[Kromosom] = []

    def run(self, callback=None) -> List[Kromosom]:
        """
        Jalankan AG untuk n_hari hari secara independen.
        Setiap hari menghasilkan satu kromosom terbaik.
        Kembalikan list kromosom terbaik [hari1, hari2, ..., hari7].
        """
        hasil_7_hari = []
        self.history_fitness = []
        self.history_best    = []

        for hari in range(self.n_hari):
            kromosom_terbaik, hist = self._run_satu_hari(hari, callback)
            hasil_7_hari.append(kromosom_terbaik)
            self.history_fitness.extend(hist["avg"])
            self.history_best.extend(hist["best"])

        return hasil_7_hari

    def _run_satu_hari(self, hari: int, callback=None):
        """
        Jalankan AG untuk satu hari (satu kromosom terbaik).
        """
        # ── Inisialisasi Populasi (Constrained) ────────────────────
        populasi = init_populasi(self.kb, self.pop_size)
        self.populasi = populasi

        hist_avg  = []
        hist_best = []

        for gen_idx in range(self.n_generasi):
            offspring = list(populasi)  # salin populasi saat ini

            # ── Crossover ──────────────────────────────────────────
            random.shuffle(populasi)
            for i in range(0, len(populasi) - 1, 2):
                if random.random() < self.crossover_rate:
                    c1, c2 = two_point_crossover(populasi[i], populasi[i+1])
                    offspring.extend([c1, c2])

            # ── Directed Mutation (RM 2b) ──────────────────────────
            mutant_pool = []
            for kromo in populasi:
                mutant = directed_mutation(kromo, self.kb, self.mutation_rate)
                mutant_pool.append(mutant)
            offspring.extend(mutant_pool)

            # ── Seleksi ────────────────────────────────────────────
            populasi = seleksi_rank_based(offspring, self.pop_size)

            # ── Log ────────────────────────────────────────────────
            best_fit = populasi[0].fitness
            avg_fit  = sum(k.fitness for k in populasi) / len(populasi)
            hist_best.append(best_fit)
            hist_avg.append(avg_fit)

            # Callback untuk update progress di Streamlit
            if callback:
                callback(hari=hari+1, generasi=gen_idx+1,
                         best=best_fit, avg=avg_fit)

        return populasi[0], {"best": hist_best, "avg": hist_avg}


# ═══════════════════════════════════════════════════════════════════
# VERIFIKASI CONSTRAINT (untuk debugging & laporan)
# ═══════════════════════════════════════════════════════════════════

def verifikasi_constraint(kromosom: Kromosom, kb: KnowledgeBase) -> Dict:
    """
    Verifikasi bahwa setiap gen dalam kromosom memenuhi hard constraint
    waktu makan. Mengembalikan laporan detail per gen.
    """
    pool_b_ids = {b.id for b in kb.get_pool(WaktuMakan.PAGI)}
    pool_l_ids = {b.id for b in kb.get_pool(WaktuMakan.SIANG)}
    pool_d_ids = {b.id for b in kb.get_pool(WaktuMakan.MALAM)}

    pool_map = {
        WaktuMakan.PAGI:  pool_b_ids,
        WaktuMakan.SIANG: pool_l_ids,
        WaktuMakan.MALAM: pool_d_ids,
    }

    hasil = []
    semua_valid = True

    for posisi, bahan in enumerate(kromosom.gen):
        waktu    = GEN_WAKTU_MAP[posisi]
        valid    = bahan.id in pool_map[waktu]
        label_wm = {"B": "Pagi", "L": "Siang", "D": "Malam"}[waktu]
        gen_label = f"g{posisi+1}"

        if not valid:
            semua_valid = False

        hasil.append({
            "gen":    gen_label,
            "waktu":  label_wm,
            "nama":   bahan.nama,
            "valid":  valid,
        })

    return {"semua_valid": semua_valid, "detail": hasil}
