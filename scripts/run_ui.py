from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


if __name__ == "__main__":
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app/ui_streamlit.py"], check=True)
