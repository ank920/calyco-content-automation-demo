# test_clear.py
import shutil, os
from pathlib import Path
ROOT = Path(".").resolve()
OUT = ROOT / "outputs"

def _on_rm_error(func, path, exc_info):
    try:
        os.chmod(path, 0o666)
    except Exception:
        pass
    try:
        func(path)
    except Exception:
        try:
            if os.path.isfile(path):
                os.remove(path)
        except Exception:
            pass

def quick_clear():
    for child in list(OUT.iterdir()):
        try:
            if child.is_dir():
                shutil.rmtree(child, onerror=_on_rm_error)
            else:
                child.unlink()
        except Exception as e:
            print("Failed:", child, e)

if __name__ == "__main__":
    quick_clear()
    print("Done")
