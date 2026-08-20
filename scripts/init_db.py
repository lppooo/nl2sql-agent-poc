from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.bootstrap import build_sample_database


if __name__ == "__main__":
    db_path = build_sample_database()
    print(f"database_ready={db_path}")
