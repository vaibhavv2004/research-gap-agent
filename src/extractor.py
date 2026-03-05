import json

def build_extraction_prompt(text: str) -> str:
    # Keep prompt small-ish (LLM context control)
    snippet = text[:12000]

    schema = {
        "paper_title": "",
        "task": "",
        "problem_setting": "",
        "method_summary": "",
        "datasets": [],
        "metrics": [],
        "baselines_or_compared_models": [],
        "experiments_present": True,
        "ablation_present": False,
        "robustness_or_safety_eval_present": False,
        "limitations_present": False,
        "key_claims": []
    }

    return f"""
Extract information from the paper text and return ONLY JSON matching this schema exactly.

Schema:
{json.dumps(schema, indent=2)}

Paper text:
\"\"\"{snippet}\"\"\"
""".strip()