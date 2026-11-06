"""Generate natural US English MP3s; keep existing audio intact on failure."""
import concurrent.futures
import json
import pathlib
import re
import shutil
import subprocess
import tempfile
import time
from gtts import gTTS

root = pathlib.Path(__file__).resolve().parents[1]
html = (root / "index.html").read_text()
items = re.findall(r'word: "([^"]+)"[\\s\\S]*?exampleEn: "([^"]+)"', html)
assert len(items) == 52, f"Unexpected vocabulary count: {len(items)}"
jobs = [(word, kind, text) for word, sentence in items
        for kind, text in (("word", word), ("sentence", sentence))]

def generate(job):
    word, kind, text = job
    path = output / f"{word}-{kind}.mp3"
    for attempt in range(4):
        try:
            gTTS(text=text, lang="en", tld="us", slow=False, timeout=(15, 60)).save(str(path))
            duration = subprocess.check_output(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "csv=p=0", str(path)], text=True)
            assert float(duration) > 0.2
            print(f"Validated {word}-{kind}", flush=True)
            return
        except Exception:
            if attempt == 3:
                raise
            time.sleep(3 * (attempt + 1))

with tempfile.TemporaryDirectory() as temp:
    output = pathlib.Path(temp)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(generate, jobs))
    for path in output.glob("*.mp3"):
        shutil.copy2(path, root / "audio" / path.name)
html = html.replace("kind + '.mp3'", "kind + '.mp3?v=natural-us-1'")
(root / "index.html").write_text(html)
print(f"Generated and validated {len(jobs)} natural US English recordings")
