# db_utils.py
# Simple SQLite wrapper to store encrypted evidence and event hashes.

import sqlite3
import os
from typing import Optional

DB_PATH = os.path.join(os.getcwd(), "milbaster.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
      CREATE TABLE IF NOT EXISTS evidence (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_hash TEXT UNIQUE,
        encrypted_evidence BLOB,
        created_at INTEGER
      );
    """)
    c.execute("""
      CREATE TABLE IF NOT EXISTS trust_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        node_id TEXT,
        trust_score INTEGER,
        reason TEXT,
        ts INTEGER
      );
    """)
    conn.commit()
    conn.close()

def save_evidence(event_hash: str, encrypted_blob: bytes, ts: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO evidence (event_hash, encrypted_evidence, created_at) VALUES (?,?,?)",
              (event_hash, encrypted_blob, ts))
    conn.commit()
    conn.close()

def save_trust(node_id: str, trust_score: int, reason: str, ts: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO trust_history (node_id, trust_score, reason, ts) VALUES (?,?,?,?)",
              (node_id, trust_score, reason, ts))
    conn.commit()
    conn.close()
