import feedparser
import urllib.parse
from typing import List, Dict, Any

ARXIV_API = "http://export.arxiv.org/api/query"

def build_arxiv_url(query: str, max_results: int = 25, start: int = 0) -> str:
    params = {
        "search_query": query,
        "start": str(start),
        "max_results": str(max_results),
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    return ARXIV_API + "?" + urllib.parse.urlencode(params)

def fetch_arxiv_papers(query: str, max_results: int = 25) -> List[Dict[str, Any]]:
    url = build_arxiv_url(query=query, max_results=max_results)
    feed = feedparser.parse(url)

    papers: List[Dict[str, Any]] = []
    for entry in feed.entries:
        arxiv_id = entry.id.split("/abs/")[-1].strip()
        title = " ".join(entry.title.split())
        summary = " ".join(entry.summary.split())

        authors = ", ".join([a.name for a in entry.authors]) if hasattr(entry, "authors") else ""
        published = entry.published if hasattr(entry, "published") else ""

        # Get primary category (best effort)
        primary_category = ""
        if hasattr(entry, "arxiv_primary_category"):
            primary_category = entry.arxiv_primary_category.get("term", "")

        # PDF link
        pdf_url = ""
        if hasattr(entry, "links"):
            for link in entry.links:
                if getattr(link, "type", "") == "application/pdf":
                    pdf_url = link.href
                    break
        if not pdf_url:
            pdf_url = entry.id.replace("/abs/", "/pdf/") + ".pdf"

        papers.append({
            "arxiv_id": arxiv_id,
            "title": title,
            "authors": authors,
            "published": published,
            "summary": summary,
            "pdf_url": pdf_url,
            "primary_category": primary_category,
        })

    return papers