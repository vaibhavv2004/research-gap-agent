import hashlib
import json

def compute_email_hash(arxiv_id: str, extracted_json: dict, gap_report: dict) -> str:
    payload = {
        "arxiv_id": arxiv_id,
        "extracted": extracted_json,
        "gaps": gap_report,
    }
    raw = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()