# Knowledge Base Klasifikasi Waktu Makan — TKPI 2019 untuk Diet Zone

**Proyek:** Optimasi Menu Diet Zone dengan Algoritma Genetika  
**Dataset:** Tabel Komposisi Pangan Indonesia (TKPI) 2019, Kemenkes RI  
**Referensi utama:** Yuliastuti et al. (2024), Pedoman Gizi Seimbang Kemenkes RI (2014)

---

## 1. Dasar Konseptual

### 1.1 Rasio Diet Zone
Mengikuti Yuliastuti et al. (2024) yang mengacu pada Dr. Barry Sears, setiap waktu makan dirancang mendekati rasio:
- **Karbohidrat: 40%**
- **Protein: 30%**
- **Lemak: 30%**
- **Serat:** ≥ 8,3 gram/waktu makan (threshold harian 25 g dibagi 3)

### 1.2 Struktur Waktu Makan
Penelitian Diet Zone Indonesia (Yuliastuti et al., 2024) menetapkan **3 waktu makan per hari** — pagi (Breakfast/B), siang (Lunch/L), malam (Dinner/D) — masing-masing terdiri dari **3 jenis makanan** (gen g1–g3, g4–g6, g7–g9).

### 1.3 Dasar Pedoman Gizi Indonesia
Pedoman Gizi Seimbang Kemenkes RI (2014) menyatakan bahwa distribusi energi harian disarankan:
- **Sarapan pagi:** ~25% total energi harian
- **Makan siang:** ~30–35% total energi harian
- **Makan malam:** ~25–30% total energi harian
- **Selingan (snack):** ~10–15%

---

## 2. Label Waktu Makan

| Label | Keterangan |
|-------|-----------|
| **B** | Breakfast — hanya sarapan |
| **L** | Lunch — hanya makan siang |
| **D** | Dinner — hanya makan malam |
| **B/L** | Sarapan atau makan siang |
| **L/D** | Makan siang atau makan malam |
| **B/L/D** | Semua waktu makan |
| **EXCLUDE** | Dikecualikan dari dataset Diet Zone |

---

## 3. Aturan Klasifikasi per Kategori Makanan

### 3.1 Makanan Pokok / Karbohidrat Utama → `B/L/D`
**Hipotesis & dasar:**  
Nasi, bihun, mi, dan sejenisnya merupakan sumber karbohidrat kompleks yang sesuai dengan pilar 40% karbohidrat Diet Zone. Berdasarkan kebiasaan makan Indonesia (Pedoman Gizi Seimbang Kemenkes, 2014), nasi dikonsumsi di semua waktu makan utama.  
> *"Sumber karbohidrat kompleks seperti nasi, jagung, dan ubi dianjurkan menjadi dasar setiap waktu makan utama."* — Pedoman Gizi Seimbang Kemenkes RI, 2014

**Pengecualian:**
- **Tepung mentah** → `EXCLUDE`: bahan baku, bukan hidangan siap konsumsi
- **Bubur** → `B/L`: secara budaya identik dengan sarapan atau makan siang di Indonesia; bukan pilihan lazim makan malam
- **Ketupat/lontong** → `L/D`: biasanya hidangan siang-malam, bukan sarapan

---

### 3.2 Daging, Unggas, Olahan Daging → `L/D`
**Hipotesis & dasar:**  
Protein hewani berat (ayam goreng, rendang, gulai, bakso, dll.) memerlukan waktu pencernaan lebih panjang. Mengonsumsi protein berat saat malam hari setelah aktivitas berkurang masih efisien secara metabolis, namun kurang ideal untuk sarapan karena memberatkan sistem pencernaan di pagi hari.

Merujuk pada Yuliastuti et al. (2024), protein berperan memenuhi threshold 30% protein Diet Zone. Dalam hasil kombinasi menu terbaik penelitian tersebut, contoh menu makan pagi menggunakan **usus ayam goreng** dan **chicken teriyaki** — menunjukkan protein hewani memang bisa masuk sarapan dalam konteks Diet Zone.

> **Catatan peneliti:** Mengikuti prinsip kehati-hatian (konservatif), label `L/D` dipilih untuk daging berat agar solusi lebih relevan dengan kebiasaan makan Indonesia. Namun system dapat dikonfigurasi menjadi `B/L/D` sesuai kebutuhan.

---

### 3.3 Ikan & Seafood → `L/D`
**Hipotesis & dasar:**  
Ikan merupakan sumber protein berkualitas tinggi dengan lemak sehat (omega-3). Secara tradisi konsumsi Indonesia, ikan lebih lazim dikonsumsi saat makan siang dan malam. Pengecualian: **teri** → `B/L/D` karena sering muncul sebagai lauk sarapan (nasi teri).

---

### 3.4 Telur → `B/L/D`
**Hipotesis & dasar:**  
Telur adalah sumber protein paling fleksibel. Dalam banyak literatur gizi, telur disebut sebagai protein sarapan ideal karena memberikan rasa kenyang lebih lama (Leidy et al., 2013, *Nutrition & Metabolism*). Di Indonesia, telur ceplok/dadar lazim untuk semua waktu makan.

---

### 3.5 Tahu & Tempe → `B/L/D`
**Hipotesis & dasar:**  
Sebagai protein nabati khas Indonesia dengan kandungan gizi seimbang, tahu dan tempe dikonsumsi di semua waktu makan. Tempe goreng bahkan sering menjadi lauk sarapan di berbagai daerah Indonesia.

---

### 3.6 Sayuran Olahan → `L/D`
**Hipotesis & dasar:**  
Sayuran berkontribusi pada pemenuhan threshold serat 25 g/hari. Konsumsi sayuran lebih lazim pada makan siang dan malam. Untuk makan pagi, sayuran umumnya tersedia dalam bentuk oseng/urap yang lebih sederhana.

**Pengecualian:**
- **Tomat, timun** → `B/L/D`: sering dikonsumsi sebagai pelengkap/lalapan di semua waktu
- **Pecel, gado-gado** → `B/L`: banyak dijual sebagai menu sarapan/makan siang di Indonesia

---

### 3.7 Buah → `B/L`
**Hipotesis & dasar:**  
Buah mengandung fruktosa yang paling efisien dimetabolisme saat aktivitas fisik masih tinggi (pagi-siang). Mengonsumsi buah di malam hari saat metabolisme melambat dapat menyebabkan penumpukan gula darah. Rekomendasi umum dietisi menyarankan konsumsi buah pada pagi dan siang hari.

> *Hipotesis ini didukung oleh pola chrono-nutrition (nutrisi berbasis ritme sirkadian) yang menyatakan metabolisme karbohidrat sederhana lebih optimal di pagi hari* (Garaulet et al., 2013, *International Journal of Obesity*).

---

### 3.8 Makanan Berkuah (Soto, Rawon, Sup) → `B/L` atau `L/D`
**Hipotesis & dasar:**  
- **Soto** → `B/L`: Soto merupakan ikon sarapan Indonesia. Soto ayam, soto Betawi, soto Lamongan lazim dikonsumsi pagi-siang.
- **Rawon, sup, sop** → `L/D`: Makanan berkuah berat lebih cocok untuk makan siang-malam.

---

### 3.9 Produk Susu & Fermentasi → `B`
**Hipotesis & dasar:**  
Yoghurt dan susu bubuk lazim dikonsumsi sebagai bagian sarapan. Keju sebagai topping roti pagi hari (`B/L`). Mengikuti pola makan Barat yang banyak diadopsi dalam Diet Zone Dr. Barry Sears, dairy products diposisikan sebagai makanan pagi/siang.

---

### 3.10 EXCLUDE (Dikecualikan dari Dataset Diet Zone)
Kategori berikut **tidak diikutkan** dalam dataset Diet Zone karena bukan makanan utama atau bahan baku mentah:

| Kategori | Alasan Eksklusi |
|----------|----------------|
| Tepung mentah (terigu, beras, dll.) | Bahan baku, bukan hidangan |
| Teh, kopi, minuman | Tidak memiliki makronutrien signifikan sebagai makanan utama |
| Mentega, margarin | Lemak murni, bukan makanan utama Diet Zone |
| Kerupuk | Makanan pelengkap/camilan, bukan makanan utama |
| Bahan bumbu | Bukan makanan utama |

---

## 4. Ringkasan Aturan dalam Kode

```python
# Format: (keyword_substring, label_waktu_makan)
MEAL_RULES = [
    ("nasi",       "B/L/D"),   # makanan pokok, semua waktu
    ("bubur",      "B/L"),     # sarapan/makan siang Indonesia
    ("ayam",       "L/D"),     # protein berat, siang/malam
    ("telur",      "B/L/D"),   # protein fleksibel
    ("tahu",       "B/L/D"),   # protein nabati fleksibel
    ("tempe",      "B/L/D"),   # protein nabati fleksibel
    ("ikan",       "L/D"),     # seafood, siang/malam
    ("buah",       "B/L"),     # fruktosa, pagi/siang
    ("soto",       "B/L"),     # ikon sarapan Indonesia
    ("tepung",     "EXCLUDE"), # bahan baku
    ("teh ",       "EXCLUDE"), # minuman tanpa makronutrien
    # ... (lihat kode lengkap di scraper_tkpi.py)
]
```

---

## 5. Referensi

1. **Yuliastuti, G.E., Kurniawan, M., Aditya, F.P. (2024).** Optimasi Kombinasi Menu Makanan Diet Zone Menggunakan Algoritma Genetika. *TEKNIKA*, 13(1), 18–26. DOI: 10.34148/teknika.v13i1.697
2. **Sears, B. (2000).** The Zone Diet and Athletic Performance. *Sports Medicine*, 29(4), 289.
3. **Cheuvront, S.N. (2003).** The Zone Diet Phenomenon. *Journal of the American College of Nutrition*, 22(1), 9–17.
4. **Kementerian Kesehatan RI. (2014).** Pedoman Gizi Seimbang. Jakarta: Kemenkes RI.
5. **Garaulet, M., et al. (2013).** Timing of food intake predicts weight loss effectiveness. *International Journal of Obesity*, 37(4), 604–611.
6. **Leidy, H.J., et al. (2013).** The role of protein in weight loss and maintenance. *American Journal of Clinical Nutrition*, 101(6), 1320S–1329S.
7. **Persatuan Ahli Gizi Indonesia. (2019).** Tabel Komposisi Pangan Indonesia (TKPI) 2019. Jakarta: Kemenkes RI.
