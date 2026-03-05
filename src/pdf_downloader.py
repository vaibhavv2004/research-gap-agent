from pathlib import Path
import requests

def download_pdf(pdf_url: str, out_path: Path, timeout: int = 30) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    r = requests.get(pdf_url, stream=True, timeout=timeout)
    r.raise_for_status()

    with open(out_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024 * 256):
            if chunk:
                f.write(chunk)

    return out_path