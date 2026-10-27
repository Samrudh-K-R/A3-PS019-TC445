"""Ingestion: SQLite schema + rows, CSV in chunks. Yields (source, column, row_index, value)."""
import os
import sqlite3
import pandas as pd

CHUNK = 10_000
SKIP_TYPES = ("BOOL", "BOOLEAN", "DATE", "DATETIME", "TIMESTAMP", "BLOB", "REAL", "FLOAT", "DOUBLE")


def iter_csv(path, chunksize=CHUNK):
    src = os.path.basename(path)
    offset = 0
    for chunk in pd.read_csv(path, dtype=str, keep_default_na=False, chunksize=chunksize):
        for col in chunk.columns:
            for i, v in enumerate(chunk[col].tolist()):
                yield src, col, offset + i, v
        offset += len(chunk)


def db_schema(path):
    """Return {table: [(column, declared_type), ...]} using PRAGMA table_info."""
    con = sqlite3.connect(path)
    try:
        tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        return {t: [(c[1], (c[2] or "").upper()) for c in con.execute(f'PRAGMA table_info("{t}")')] for t in tables}
    finally:
        con.close()


def iter_db(path, skip_types=SKIP_TYPES):
    """Schema-first: skip columns whose declared type cannot hold the target classes."""
    schema = db_schema(path)
    con = sqlite3.connect(path)
    try:
        for table, cols in schema.items():
            keep = [c for c, t in cols if not any(s in t for s in skip_types)]
            skipped = [c for c, t in cols if c not in keep]
            if not keep:
                continue
            q = ", ".join(f'"{c}"' for c in keep)
            for i, row in enumerate(con.execute(f'SELECT {q} FROM "{table}" ORDER BY rowid')):
                for c, v in zip(keep, row):
                    yield f"{os.path.basename(path)}:{table}", c, i, ("" if v is None else str(v))
    finally:
        con.close()
