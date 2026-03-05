import sqlite3
from pathlib import Path
from typing import Dict, Any, List
import json
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "agent.db"


def get_conn() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    conn = get_conn()
    cur = conn.cursor()

    # Create table if not exists
    cur.execute("""
        CREATE TABLE IF NOT EXISTS papers (
            arxiv_id TEXT PRIMARY KEY,
            title TEXT,
            authors TEXT,
            published TEXT,
            summary TEXT,
            pdf_url TEXT,
            primary_category TEXT,
            processed INTEGER DEFAULT 0,
            email_hash TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ---- MIGRATION: Add new columns if they don't exist ----
    existing_cols = set(r[1] for r in cur.execute("PRAGMA table_info(papers)").fetchall())

    if "pdf_path" not in existing_cols:
        cur.execute("ALTER TABLE papers ADD COLUMN pdf_path TEXT")

    if "raw_text" not in existing_cols:
        cur.execute("ALTER TABLE papers ADD COLUMN raw_text TEXT")

    if "text_extracted" not in existing_cols:
        cur.execute("ALTER TABLE papers ADD COLUMN text_extracted INTEGER DEFAULT 0")

    if "extracted_json" not in existing_cols:
        cur.execute("ALTER TABLE papers ADD COLUMN extracted_json TEXT")

    if "gap_report" not in existing_cols:
        cur.execute("ALTER TABLE papers ADD COLUMN gap_report TEXT")

    if "emailed" not in existing_cols:
        cur.execute("ALTER TABLE papers ADD COLUMN emailed INTEGER DEFAULT 0")

    if "email_sent_at" not in existing_cols:
        cur.execute("ALTER TABLE papers ADD COLUMN email_sent_at TEXT")

    conn.commit()
    conn.close()


def upsert_paper(p: Dict[str, Any]) -> bool:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT OR IGNORE INTO papers (
            arxiv_id, title, authors, published, summary,
            pdf_url, primary_category, processed, email_hash
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, NULL)
    """, (
        p["arxiv_id"],
        p.get("title", ""),
        p.get("authors", ""),
        p.get("published", ""),
        p.get("summary", ""),
        p.get("pdf_url", ""),
        p.get("primary_category", "")
    ))

    inserted = cur.rowcount > 0
    conn.commit()
    conn.close()
    return inserted


def list_latest(limit: int = 10) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT arxiv_id, title, published, primary_category, pdf_url
        FROM papers
        ORDER BY published DESC
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()

    return [
        {
            "arxiv_id": r[0],
            "title": r[1],
            "published": r[2],
            "primary_category": r[3],
            "pdf_url": r[4],
        }
        for r in rows
    ]


def count_papers() -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM papers")
    n = cur.fetchone()[0]
    conn.close()
    return int(n)


def get_unextracted_papers(limit: int = 5) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT arxiv_id, title, pdf_url
        FROM papers
        WHERE text_extracted = 0
        ORDER BY published DESC
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()

    return [{"arxiv_id": r[0], "title": r[1], "pdf_url": r[2]} for r in rows]


def save_extracted_text(arxiv_id: str, pdf_path: str, raw_text: str) -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE papers
        SET pdf_path = ?, raw_text = ?, text_extracted = 1
        WHERE arxiv_id = ?
    """, (pdf_path, raw_text, arxiv_id))
    conn.commit()
    conn.close()


def get_ready_for_llm(limit: int = 5) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT arxiv_id, title, raw_text
        FROM papers
        WHERE text_extracted = 1 AND processed = 0
        ORDER BY published DESC
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()

    return [{"arxiv_id": r[0], "title": r[1], "raw_text": r[2]} for r in rows]


def save_llm_outputs(arxiv_id: str, extracted_json: dict, gap_report: dict) -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE papers
        SET extracted_json = ?, gap_report = ?, processed = 1
        WHERE arxiv_id = ?
    """, (json.dumps(extracted_json), json.dumps(gap_report), arxiv_id))
    conn.commit()
    conn.close()


def get_unemailed_reports(limit: int = 10) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT arxiv_id, title, published, pdf_url, extracted_json, gap_report
        FROM papers
        WHERE processed = 1 AND emailed = 0
        ORDER BY published DESC
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()

    out: List[Dict[str, Any]] = []
    for r in rows:
        out.append({
            "arxiv_id": r[0],
            "title": r[1],
            "published": r[2],
            "pdf_url": r[3],
            "extracted_json": json.loads(r[4]) if r[4] else {},
            "gap_report": json.loads(r[5]) if r[5] else {},
        })
    return out


def mark_emailed(arxiv_ids: List[str]) -> None:
    conn = get_conn()
    cur = conn.cursor()
    ts = datetime.utcnow().isoformat()

    for pid in arxiv_ids:
        cur.execute("""
            UPDATE papers
            SET emailed = 1, email_sent_at = ?
            WHERE arxiv_id = ?
        """, (ts, pid))

    conn.commit()
    conn.close()