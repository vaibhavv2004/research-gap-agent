from typing import List, Dict, Any
from html import escape


def build_email_subject(n: int) -> str:
    return f"Daily Research Gap Report — {n} new papers"


def severity_score(gap_report: Dict[str, Any]) -> int:
    """
    Simple scoring:
    +2 for each gap (up to 6)
    +1 for each suggested experiment (up to 4)
    """
    gaps = gap_report.get("gaps", []) or []
    exps = gap_report.get("suggested_experiments", []) or []
    return min(len(gaps), 6) * 2 + min(len(exps), 4) * 1


def severity_label(score: int) -> str:
    if score >= 12:
        return "HIGH"
    if score >= 7:
        return "MEDIUM"
    return "LOW"


def _pill_html(label: str) -> str:
    # basic color mapping
    if label == "HIGH":
        bg = "#ffdddd"
        fg = "#a40000"
    elif label == "MEDIUM":
        bg = "#fff2cc"
        fg = "#7a5d00"
    else:
        bg = "#ddffdd"
        fg = "#006b1b"

    return f"""
    <span style="display:inline-block;padding:4px 10px;border-radius:999px;
                 background:{bg};color:{fg};font-weight:700;font-size:12px;">
        {label}
    </span>
    """.strip()


def build_email_body_text(items: List[Dict[str, Any]]) -> str:
    # plain text fallback (optional but good)
    lines = []
    lines.append("Daily Research Gap Detection Report\n")
    lines.append(f"New papers with gap analysis: {len(items)}\n")
    lines.append("-" * 60)

    for i, it in enumerate(items, start=1):
        extracted = it.get("extracted_json", {}) or {}
        gaps = it.get("gap_report", {}) or {}
        score = severity_score(gaps)
        sev = severity_label(score)

        lines.append(f"\n{i}) [{sev}] {it['title']}")
        lines.append(f"arXiv: {it['arxiv_id']}")
        lines.append(f"Published: {it['published']}")
        lines.append(f"PDF: {it['pdf_url']}")

        lines.append("\nExtracted:")
        lines.append(f"- Task: {extracted.get('task', '')}")
        lines.append(f"- Datasets: {', '.join(extracted.get('datasets', []))}")
        lines.append(f"- Metrics: {', '.join(extracted.get('metrics', []))}")

        lines.append("\nGaps:")
        for g in (gaps.get("gaps", []) or [])[:6]:
            lines.append(f"- {g}")

        lines.append("\nSuggested Experiments:")
        for e in (gaps.get("suggested_experiments", []) or [])[:4]:
            lines.append(f"- {e}")

        lines.append("-" * 60)

    return "\n".join(lines)


def build_email_body_html(items: List[Dict[str, Any]]) -> str:
    # Sort by severity score (desc)
    scored = []
    for it in items:
        gaps = it.get("gap_report", {}) or {}
        score = severity_score(gaps)
        scored.append((score, it))
    scored.sort(key=lambda x: x[0], reverse=True)

    top3 = scored[:3]
    rest = scored[3:]

    def paper_block(score: int, it: Dict[str, Any]) -> str:
        extracted = it.get("extracted_json", {}) or {}
        gaps = it.get("gap_report", {}) or {}
        sev = severity_label(score)

        title = escape(it.get("title", ""))
        arxiv_id = escape(it.get("arxiv_id", ""))
        published = escape(it.get("published", ""))
        pdf_url = escape(it.get("pdf_url", ""))

        task = escape(str(extracted.get("task", "")))
        datasets = extracted.get("datasets", []) or []
        metrics = extracted.get("metrics", []) or []

        gaps_list = gaps.get("gaps", []) or []
        exps_list = gaps.get("suggested_experiments", []) or []

        ds_html = "".join(f"<li>{escape(str(d))}</li>" for d in datasets[:6]) or "<li>—</li>"
        met_html = "".join(f"<li>{escape(str(m))}</li>" for m in metrics[:6]) or "<li>—</li>"
        gap_html = "".join(f"<li>{escape(str(g))}</li>" for g in gaps_list[:6]) or "<li>—</li>"
        exp_html = "".join(f"<li>{escape(str(e))}</li>" for e in exps_list[:4]) or "<li>—</li>"

        return f"""
        <div style="border:1px solid #e6e6e6;border-radius:14px;padding:16px;margin:14px 0;">
          <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
            <div style="font-size:16px;font-weight:800;line-height:1.3;">{title}</div>
            {_pill_html(sev)}
            <span style="font-size:12px;color:#666;">Score: {score}</span>
          </div>

          <div style="margin-top:8px;font-size:13px;color:#333;">
            <div><b>arXiv:</b> {arxiv_id}</div>
            <div><b>Published:</b> {published}</div>
            <div><b>PDF:</b> <a href="{pdf_url}">{pdf_url}</a></div>
          </div>

          <div style="margin-top:12px;">
            <div style="font-weight:800;">Extracted</div>
            <div style="margin-top:6px;"><b>Task:</b> {task if task else "—"}</div>
            <div style="display:flex;gap:24px;flex-wrap:wrap;margin-top:6px;">
              <div style="min-width:240px;">
                <div style="font-weight:700;">Datasets</div>
                <ul style="margin:6px 0 0 18px;">{ds_html}</ul>
              </div>
              <div style="min-width:240px;">
                <div style="font-weight:700;">Metrics</div>
                <ul style="margin:6px 0 0 18px;">{met_html}</ul>
              </div>
            </div>
          </div>

          <div style="margin-top:12px;">
            <div style="font-weight:800;">Gaps</div>
            <ul style="margin:6px 0 0 18px;">{gap_html}</ul>
          </div>

          <div style="margin-top:12px;">
            <div style="font-weight:800;">Suggested Experiments</div>
            <ul style="margin:6px 0 0 18px;">{exp_html}</ul>
          </div>
        </div>
        """.strip()

    top_html = "".join(paper_block(s, it) for s, it in top3)
    rest_html = "".join(paper_block(s, it) for s, it in rest)

    return f"""
    <div style="font-family:Arial,Helvetica,sans-serif;max-width:900px;margin:0 auto;">
      <h2 style="margin:0 0 6px 0;">Daily Research Gap Detection Report</h2>
      <div style="color:#555;margin-bottom:16px;">New papers with gap analysis: <b>{len(items)}</b></div>

      <h3 style="margin:18px 0 8px 0;">🔥 Top 3 by Severity</h3>
      {top_html if top_html else "<div>—</div>"}

      <h3 style="margin:18px 0 8px 0;">All Remaining</h3>
      {rest_html if rest_html else "<div>—</div>"}

      <div style="color:#888;font-size:12px;margin-top:18px;">
        Generated automatically by Research Gap Agent.
      </div>
    </div>
    """.strip()