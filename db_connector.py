"""
db_connector.py
───────────────
Modul koneksi ke database MySQL diet_zone.
Menyediakan fungsi untuk mengambil pool bahan pangan
dari view v_ag_breakfast, v_ag_lunch, v_ag_dinner.
"""

import mysql.connector
import pandas as pd
from typing import Optional

# ── Konfigurasi default (sesuaikan di Streamlit sidebar) ──────────
DEFAULT_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "database": "diet_zone",
    "user":     "root",
    "password": "",
}


def get_connection(config: dict = None):
    """Buat koneksi ke database MySQL."""
    cfg = config or DEFAULT_CONFIG
    return mysql.connector.connect(**cfg)


def test_connection(config: dict) -> tuple[bool, str]:
    """
    Test koneksi database.
    Kembalikan (True, pesan) jika berhasil, (False, error) jika gagal.
    """
    try:
        conn = get_connection(config)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM bahan_pangan")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return True, f"Terhubung — {count} bahan pangan tersedia"
    except Exception as e:
        return False, str(e)


def load_pool_as_df(conn, view_name: str) -> pd.DataFrame:
    """Ambil pool dari view database sebagai DataFrame."""
    query = f"""
        SELECT id, kode, nama, kelompok_id,
               COALESCE(karbohidrat_g, 0)   AS karbohidrat_g,
               COALESCE(protein_g, 0)        AS protein_g,
               COALESCE(lemak_g, 0)          AS lemak_g,
               COALESCE(serat_g, 0)          AS serat_g,
               COALESCE(pct_karbohidrat, 0)  AS pct_karbohidrat,
               COALESCE(pct_protein, 0)      AS pct_protein,
               COALESCE(pct_lemak, 0)        AS pct_lemak
        FROM `{view_name}`
        ORDER BY id
    """
    return pd.read_sql(query, conn)


def load_all_pools(conn) -> dict:
    """
    Ambil ketiga pool dari database.
    Kembalikan dict berisi DataFrame breakfast, lunch, dinner.
    """
    return {
        "breakfast": load_pool_as_df(conn, "v_ag_breakfast"),
        "lunch":     load_pool_as_df(conn, "v_ag_lunch"),
        "dinner":    load_pool_as_df(conn, "v_ag_dinner"),
    }


def load_threshold(conn) -> dict:
    """Ambil nilai threshold Diet Zone dari database."""
    query = "SELECT nama_parameter, nilai FROM diet_zone_threshold"
    df = pd.read_sql(query, conn)
    return dict(zip(df["nama_parameter"], df["nilai"].astype(float)))
