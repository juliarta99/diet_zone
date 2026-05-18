"""
Scraper Data Tabel Komposisi Pangan Indonesia (TKPI) 2019
Sumber: https://www.andrafarm.com/_andra.php?_i=daftar-tkpi

Cara pakai:
    pip install requests beautifulsoup4 lxml
    python scraper_tkpi.py

Output:
    tkpi_raw.csv       — semua 1.148 bahan pangan (karbohidrat, protein, lemak, serat)
    tkpi_diet_zone.csv — filter hanya bahan pangan siap makan + label waktu makan

PERBAIKAN v3:
    - URL pagination yang benar: no1, no2, dan kk harus berubah setiap halaman
    - Page 2 : no1=1,   no2=40,   kk=2
    - Page 3 : no1=41,  no2=80,   kk=3
    - Page 4 : no1=81,  no2=120,  kk=4  dst.
    (Ditemukan dari analisis link halaman di HTML asli)
"""

import requests
from bs4 import BeautifulSoup
import csv, time, sys, re

# ── Konfigurasi ───────────────────────────────────────────────────────────────
BASE_URL   = "https://www.andrafarm.com/_andra.php"
TOTAL_DATA = 1148
PER_HAL    = 40
DELAY      = 1.5
RAW_CSV    = "tkpi_raw.csv"
DIET_CSV   = "tkpi_diet_zone.csv"

HEADERS = {
    "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8",
    "Referer":         "https://www.andrafarm.com/_andra.php?_i=daftar-tkpi",
}

COL_NO=0; COL_KODE=1; COL_NAMA=2
COL_PROTEIN=5; COL_LEMAK=6; COL_KARBO=7; COL_SERAT=8
COL_OLAHAN=25; COL_KELOMPOK=26; COL_SUMBER=27

MEAL_RULES = [
    # ── SEREALIA & NASI → B/L/D (karbohidrat utama, cocok semua waktu) ────────
    ("nasi",             "B/L/D"),
    ("bubur",            "B/L"),   # bubur identik sarapan/makan siang di Indonesia
    ("bihun",            "B/L/D"),
    ("mi ",              "B/L/D"),
    ("mie ",             "B/L/D"),
    ("makaroni",         "L/D"),
    ("ketan",            "B/L"),
    ("tepung",           "EXCLUDE"),  # bahan baku mentah, bukan makanan jadi
    ("maizena",          "EXCLUDE"),
    ("roti",             "B/L"),
    ("biskuit",          "B"),
    ("kue",              "B"),
    ("cake",             "B"),
    ("bolu",             "B"),
    ("tapai",            "B/L"),
    ("ketupat",          "L/D"),
    ("lontong",          "B/L"),

    # ── DAGING & UNGGAS ────────────────────────────────────────────────────────
    ("ayam",             "L/D"),
    ("bebek",            "L/D"),
    ("sapi",             "L/D"),
    ("kambing",          "L/D"),
    ("babi",             "L/D"),
    ("hati",             "L/D"),
    ("usus",             "L/D"),
    ("jeroan",           "L/D"),
    ("daging",           "L/D"),
    ("kornet",           "B/L"),
    ("sosis",            "B/L"),
    ("nugget",           "B/L/D"),
    ("burger",           "L/D"),
    ("bakso",            "L/D"),
    ("rendang",          "L/D"),
    ("semur",            "L/D"),
    ("gulai",            "L/D"),
    ("kalio",            "L/D"),
    ("opor",             "L/D"),
    ("sate",             "L/D"),
    ("tongseng",         "L/D"),

    # ── IKAN & SEAFOOD ─────────────────────────────────────────────────────────
    ("ikan",             "L/D"),
    ("udang",            "L/D"),
    ("cumi",             "L/D"),
    ("kepiting",         "L/D"),
    ("kerang",           "L/D"),
    ("lele",             "L/D"),
    ("bandeng",          "L/D"),
    ("tongkol",          "L/D"),
    ("kakap",            "L/D"),
    ("gurame",           "L/D"),
    ("salmon",           "L/D"),
    ("tuna",             "L/D"),
    ("teri",             "B/L/D"),
    ("sarden",           "B/L"),
    ("pindang",          "L/D"),
    ("pecel lele",       "D"),
    ("abon",             "B/L/D"),

    # ── TELUR ──────────────────────────────────────────────────────────────────
    ("telur",            "B/L/D"),  # fleksibel semua waktu
    ("omelet",           "B/L"),

    # ── KACANG-KACANGAN & TAHU TEMPE ──────────────────────────────────────────
    ("tahu",             "B/L/D"),
    ("tempe",            "B/L/D"),
    ("kacang",           "B/L/D"),
    ("edamame",          "L/D"),
    ("buncis",           "L/D"),
    ("kedelai",          "L/D"),

    # ── SAYURAN ────────────────────────────────────────────────────────────────
    # Sayuran mentah → EXCLUDE (bahan baku, bukan hidangan)
    ("bayam",            "L/D"),
    ("kangkung",         "L/D"),
    ("sawi",             "L/D"),
    ("brokoli",          "L/D"),
    ("wortel",           "L/D"),
    ("labu",             "L/D"),
    ("terong",           "L/D"),
    ("tomat",            "B/L/D"),
    ("timun",            "B/L/D"),
    ("selada",           "B/L"),
    ("kubis",            "L/D"),
    ("kol",              "L/D"),
    ("singkong",         "B/L"),
    ("ubi",              "B/L"),
    ("kentang",          "B/L/D"),
    ("jagung",           "B/L/D"),
    ("rebung",           "L/D"),
    ("tauge",            "L/D"),
    ("oyong",            "L/D"),
    ("gambas",           "L/D"),
    ("pare",             "L/D"),
    ("pepaya muda",      "L/D"),
    ("nangka muda",      "L/D"),
    ("capcay",           "L/D"),
    ("tumis",            "L/D"),
    ("oseng",            "L/D"),
    ("pecel",            "B/L"),
    ("gado",             "L"),
    ("ketoprak",         "L"),
    ("lotek",            "L"),
    ("urap",             "L/D"),

    # ── BUAH ───────────────────────────────────────────────────────────────────
    # Buah segar → B/L (snack pagi/siang), bukan makan malam (gula fruktosa malam hari)
    ("apel",             "B/L"),
    ("pisang",           "B/L"),
    ("mangga",           "B/L"),
    ("jeruk",            "B/L"),
    ("pepaya",           "B/L"),
    ("semangka",         "B/L"),
    ("melon",            "B/L"),
    ("anggur",           "B/L"),
    ("jambu",            "B/L"),
    ("nanas",            "B/L"),
    ("alpukat",          "B/L"),
    ("durian",           "B/L"),
    ("rambutan",         "B/L"),
    ("leci",             "B/L"),
    ("manggis",          "B/L"),
    ("salak",            "B/L"),
    ("duku",             "B/L"),
    ("sawo",             "B/L"),
    ("nangka",           "B/L"),
    ("sirsak",           "B/L"),
    ("belimbing",        "B/L"),
    ("buah",             "B/L"),

    # ── MASAKAN/HIDANGAN SIAP MAKAN ────────────────────────────────────────────
    ("soto",             "B/L"),   # soto umum untuk sarapan dan makan siang
    ("rawon",            "L/D"),
    ("sop",              "L/D"),
    ("sup",              "L/D"),
    ("pempek",           "B/L"),
    ("siomay",           "L"),
    ("batagor",          "L"),
    ("martabak",         "L/D"),
    ("nasi goreng",      "B/L/D"),
    ("mie goreng",       "B/L/D"),
    ("steak",            "L/D"),
    ("teriyaki",         "L/D"),
    ("rujak",            "B/L"),
    ("gule",             "L/D"),
    ("lodeh",            "L/D"),
    ("pepes",            "L/D"),
    ("bakar",            "L/D"),
    ("goreng",           "B/L/D"),
    ("rebus",            "B/L/D"),
    ("kukus",            "B/L/D"),
    ("panggang",         "L/D"),

    # ── PRODUK SUSU & OLAHAN ───────────────────────────────────────────────────
    ("yoghurt",          "B"),
    ("keju",             "B/L"),
    ("mentega",          "EXCLUDE"),  # lemak murni, bukan makanan utama
    ("susu bubuk",       "B"),

    # ── MINUMAN & BAHAN MINUMAN → EXCLUDE dari Diet Zone food ─────────────────
    ("teh ",             "EXCLUDE"),
    ("kopi",             "EXCLUDE"),
    ("sirup",            "EXCLUDE"),
    ("minuman",          "EXCLUDE"),
    ("jus",              "B"),

    # ── BAHAN MENTAH / BUMBU → EXCLUDE ────────────────────────────────────────
    ("mentah",           "EXCLUDE"),
    ("bubuk",            "EXCLUDE"),  # selain susu bubuk sudah ditangani
    ("instan",           "B/L/D"),    # mi/bihun instan = makanan jadi
    ("kerupuk",          "EXCLUDE"),  # pelengkap/snack bukan makanan utama
    ("keripik",          "B/L"),
    ("emping",           "B/L"),
]

EXCLUDE_KELOMPOK = set()  # bisa ditambahkan: {"Bumbu", "Minuman"} dst.

session = requests.Session()
session.headers.update(HEADERS)

def fetch_page(no1, no2, kk, retries=4):
    """Fetch satu halaman dengan parameter URL yang benar."""
    params = {
        "_i":     "daftar-tkpi",
        "jobs":   "",
        "perhal": PER_HAL,
        "urut":   1,
        "asc":    "0000000000",
        "sby":    "",
        "no1":    no1,
        "no2":    no2,
        "kk":     kk,
    }
    for attempt in range(1, retries + 1):
        try:
            r = session.get(BASE_URL, params=params, timeout=30)
            r.raise_for_status()
            r.encoding = "utf-8"
            return BeautifulSoup(r.text, "lxml")
        except requests.RequestException as e:
            wait = attempt * 3
            print("    [!] Percobaan {}/{}: {}. Tunggu {}s...".format(attempt, retries, e, wait))
            time.sleep(wait)
    return None

def find_data_table(soup):
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if len(rows) < 4:
            continue
        header_text = rows[0].get_text()
        if "Nama Bahan Makanan" in header_text and "Protein" in header_text:
            return table
    return None

def parse_table(table):
    rows = table.find_all("tr")
    records = []
    for row in rows:
        cells = row.find_all(["td", "th"])
        texts = [c.get_text(strip=True) for c in cells]
        if not texts or not texts[0].isdigit():
            continue
        while len(texts) <= COL_SUMBER:
            texts.append("-")
        def v(idx):
            val = texts[idx] if idx < len(texts) else "-"
            return val if val else "-"
        records.append({
            "No":                 v(COL_NO),
            "Kode":               v(COL_KODE),
            "Nama Bahan Makanan": v(COL_NAMA),
            "Karbohidrat (g)":    v(COL_KARBO),
            "Protein (g)":        v(COL_PROTEIN),
            "Lemak (g)":          v(COL_LEMAK),
            "Serat (g)":          v(COL_SERAT),
            "Mentah/Olahan":      v(COL_OLAHAN),
            "Kelompok Makanan":   v(COL_KELOMPOK),
            "Sumber TKPI 2019":   v(COL_SUMBER),
        })
    return records

def get_meal_label(nama):
    """
    Tentukan label waktu makan berdasarkan nama makanan.
    Kembalikan 'EXCLUDE' jika bukan makanan siap makan Diet Zone.
    """
    nama_lower = nama.lower()
    for keyword, label in MEAL_RULES:
        if keyword in nama_lower:
            return label
    return "B/L/D"

def build_pages():
    """
    Bangun daftar parameter per halaman berdasarkan link yang ditemukan di HTML.
    Halaman ke-N (N>=2): no1=(N-2)*40+1, no2=(N-1)*40, kk=N
    Halaman 1 (landing): no1 tidak relevan karena menampilkan 40 pertama
    """
    pages = []
    # Dari analisis HTML:
    # Page 2 (kk=2): no1=1,   no2=40
    # Page 3 (kk=3): no1=41,  no2=80
    # Page N (kk=N): no1=(N-2)*40+1, no2=(N-1)*40
    # Total pages = 29 (kk=2 s/d kk=30)
    for kk in range(2, 31):  # kk=2 to kk=30 (29 pages)
        no1 = (kk - 2) * 40 + 1
        no2 = (kk - 1) * 40
        if no1 > TOTAL_DATA:
            break
        no2 = min(no2, TOTAL_DATA)
        pages.append((no1, no2, kk))
    return pages

def main():
    pages = build_pages()

    print("=" * 65)
    print("  Scraper TKPI 2019 v3 — URL pagination diperbaiki")
    print("=" * 65)
    print("  Target    : {} bahan pangan".format(TOTAL_DATA))
    print("  Halaman   : {} (parameter: no1, no2, kk)".format(len(pages)))
    print("  Output 1  : {} (semua data mentah)".format(RAW_CSV))
    print("  Output 2  : {} (filter Diet Zone + label waktu)".format(DIET_CSV))
    print("=" * 65)

    all_records = []
    for i, (no1, no2, kk) in enumerate(pages, 1):
        print("  Hal {:2d}/{:2d}  no1={:4d} no2={:4d} kk={:2d} ...".format(
            i, len(pages), no1, no2, kk), end=" ", flush=True)
        soup = fetch_page(no1, no2, kk)
        if soup is None:
            print("GAGAL (skip)")
            continue
        table = find_data_table(soup)
        if table is None:
            print("Tabel tidak ditemukan (skip)")
            continue
        records = parse_table(table)
        all_records.extend(records)
        print("+{:2d} | total: {:4d}".format(len(records), len(all_records)))
        if i < len(pages):
            time.sleep(DELAY)

    if not all_records:
        print("\nGAGAL: Tidak ada data.")
        sys.exit(1)

    # Deduplikasi berdasarkan Kode + Nama
    seen = set()
    unique = []
    for r in all_records:
        key = r["Kode"] + "|" + r["Nama Bahan Makanan"]
        if key not in seen:
            seen.add(key)
            unique.append(r)
    all_records = unique

    raw_fields = ["No","Kode","Nama Bahan Makanan","Karbohidrat (g)",
                  "Protein (g)","Lemak (g)","Serat (g)",
                  "Mentah/Olahan","Kelompok Makanan","Sumber TKPI 2019"]
    with open(RAW_CSV, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=raw_fields)
        w.writeheader(); w.writerows(all_records)

    diet_records = []
    excluded = []
    for r in all_records:
        label = get_meal_label(r["Nama Bahan Makanan"])
        if label == "EXCLUDE":
            excluded.append(r["Nama Bahan Makanan"])
            continue
        if r["Kelompok Makanan"] in EXCLUDE_KELOMPOK:
            excluded.append(r["Nama Bahan Makanan"])
            continue
        def parse_num(s):
            if s in ("-", "", "0"):
                return 0.0
            try:
                return float(s.replace(",", "."))
            except:
                return 0.0
        karbo  = parse_num(r["Karbohidrat (g)"])
        prot   = parse_num(r["Protein (g)"])
        lemak  = parse_num(r["Lemak (g)"])
        serat  = parse_num(r["Serat (g)"])
        total  = karbo + prot + lemak
        pct_k  = round(karbo / total * 100, 1) if total > 0 else 0
        pct_p  = round(prot  / total * 100, 1) if total > 0 else 0
        pct_l  = round(lemak / total * 100, 1) if total > 0 else 0

        diet_records.append({
            "No":                   r["No"],
            "Kode":                 r["Kode"],
            "Nama Bahan Makanan":   r["Nama Bahan Makanan"],
            "Karbohidrat (g)":      r["Karbohidrat (g)"],
            "Protein (g)":          r["Protein (g)"],
            "Lemak (g)":            r["Lemak (g)"],
            "Serat (g)":            r["Serat (g)"],
            "% Karbo":              pct_k,
            "% Protein":            pct_p,
            "% Lemak":              pct_l,
            "Waktu Makan":          label,
            "Kelompok Makanan":     r["Kelompok Makanan"],
            "Mentah/Olahan":        r["Mentah/Olahan"],
        })

    diet_fields = ["No","Kode","Nama Bahan Makanan",
                   "Karbohidrat (g)","Protein (g)","Lemak (g)","Serat (g)",
                   "% Karbo","% Protein","% Lemak",
                   "Waktu Makan","Kelompok Makanan","Mentah/Olahan"]
    with open(DIET_CSV, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=diet_fields)
        w.writeheader(); w.writerows(diet_records)

    print()
    print("=" * 65)
    print("  SELESAI!")
    print("  {} -> {} bahan pangan (semua)".format(RAW_CSV, len(all_records)))
    print("  {} -> {} bahan pangan Diet Zone".format(DIET_CSV, len(diet_records)))
    print("  Dikecualikan (EXCLUDE): {} item".format(len(excluded)))
    if len(all_records) < TOTAL_DATA:
        print("  PERINGATAN: Target {} item, berhasil {}".format(TOTAL_DATA, len(all_records)))
    print("=" * 65)

if __name__ == "__main__":
    main()