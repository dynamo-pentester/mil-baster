import sqlite3
import os

db_path = 'src/milbaster.db'
if os.path.exists(db_path):
    print(f"Database file exists: {db_path}")
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in c.fetchall()]
        print(f"Tables: {tables}")
        if 'evidence' in tables:
            c.execute("SELECT COUNT(*) FROM evidence")
            count = c.fetchone()[0]
            print(f"Evidence table has {count} rows")
        else:
            print("Evidence table does not exist")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
else:
    print(f"Database file does not exist: {db_path}")
