import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# Emails (for later)
TO_EMAIL = os.getenv("TO_EMAIL", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "")

# LLM (for later)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"

# arXiv settings (edit these!)
ARXIV_QUERY = os.getenv(
    "ARXIV_QUERY",
    # Example: last 2 days papers in cs.LG OR cs.CL with keywords
    'cat:cs.LG OR cat:cs.CL'
)
MAX_RESULTS = int(os.getenv("MAX_RESULTS", "25"))