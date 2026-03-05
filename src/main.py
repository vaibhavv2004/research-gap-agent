from pathlib import Path
import json

from .db import (
    init_db,
    upsert_paper,
    count_papers,
    list_latest,
    get_unextracted_papers,
    save_extracted_text,
    get_ready_for_llm,
    save_llm_outputs,
    get_unemailed_reports,
    mark_emailed,
)

from .config import ARXIV_QUERY, MAX_RESULTS, PROJECT_ROOT
from .arxiv_fetcher import fetch_arxiv_papers
from .pdf_downloader import download_pdf
from .pdf_parser import extract_text_pymupdf

from .llm_client import llm_json
from .extractor import build_extraction_prompt
from .gap_detector import rule_gaps, build_gap_prompt

# ✅ Correct import (HTML version)
from .report_builder import (
    build_email_subject,
    build_email_body_text,
    build_email_body_html,
)

from .emailer import send_email


def main():
    print("Initializing Research Gap Agent...")
    init_db()
    print("Database ready.")

    # STEP 2: Fetch papers
    print(f"\nFetching arXiv papers: query='{ARXIV_QUERY}', max_results={MAX_RESULTS}")
    papers = fetch_arxiv_papers(query=ARXIV_QUERY, max_results=MAX_RESULTS)

    inserted = 0
    for p in papers:
        if upsert_paper(p):
            inserted += 1

    total = count_papers()
    print(f"\nFetched: {len(papers)} | Inserted new: {inserted} | Total in DB: {total}")

    print("\nLatest papers in DB:")
    for row in list_latest(limit=5):
        print(f"- [{row['published']}] {row['arxiv_id']} | {row['primary_category']} | {row['title']}")

    # STEP 3: Download + Extract text
    print("\nStep 3: Download PDFs & Extract Text (top 5 unprocessed)")
    to_process = get_unextracted_papers(limit=5)

    pdf_dir = PROJECT_ROOT / "data" / "pdf_cache"
    pdf_dir.mkdir(parents=True, exist_ok=True)

    for item in to_process:
        arxiv_id = item["arxiv_id"]
        pdf_url = item["pdf_url"]
        safe_name = arxiv_id.replace("/", "_")
        pdf_path = pdf_dir / f"{safe_name}.pdf"

        try:
            print(f"\nDownloading: {arxiv_id}")
            download_pdf(pdf_url, pdf_path)

            print("Extracting text...")
            text = extract_text_pymupdf(pdf_path, max_pages=12)

            save_extracted_text(arxiv_id, str(pdf_path), text)
            print(f"✅ Saved text ({len(text)} chars)")

        except Exception as e:
            print(f"❌ Failed for {arxiv_id}: {e}")

    # STEP 4: LLM Extraction + Gap Detection
    print("\nStep 4: LLM Extraction + Gap Detection (top 5 ready)")
    ready = get_ready_for_llm(limit=5)

    for item in ready:
        arxiv_id = item["arxiv_id"]
        raw_text = item.get("raw_text") or ""

        if not raw_text.strip():
            print(f"⚠ Skipping {arxiv_id} (empty raw_text)")
            continue

        try:
            print(f"\nProcessing with LLM: {arxiv_id}")

            extraction_prompt = build_extraction_prompt(raw_text)
            extracted_str = llm_json(extraction_prompt)
            extracted = json.loads(extracted_str)

            rules = rule_gaps(extracted)
            gap_prompt = build_gap_prompt(extracted, rules)
            gap_str = llm_json(gap_prompt)
            gap_report = json.loads(gap_str)

            save_llm_outputs(arxiv_id, extracted, gap_report)
            print("✅ Saved extracted_json + gap_report")

        except Exception as e:
            print(f"❌ LLM processing failed for {arxiv_id}: {e}")

    # STEP 5: Email digest (no repeats)
    print("\nStep 5: Email digest (only unemailed processed papers)")
    items = get_unemailed_reports(limit=10)

    if not items:
        print("No new reports to email today ✅")
        return

    try:
        subject = build_email_subject(len(items))
        body_text = build_email_body_text(items)
        body_html = build_email_body_html(items)

        send_email(subject, body_text, body_html)
        mark_emailed([x["arxiv_id"] for x in items])

        print(f"✅ Email sent for {len(items)} papers and marked as emailed.")

    except Exception as e:
        print(f"❌ Email sending failed: {e}")


if __name__ == "__main__":
    main()