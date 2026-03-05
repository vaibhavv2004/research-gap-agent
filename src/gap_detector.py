import json

TASK_METRICS_HINTS = {
    "classification": ["accuracy", "f1", "precision", "recall", "auc"],
    "summarization": ["rouge", "bertscore"],
    "retrieval": ["mrr", "ndcg", "recall@", "precision@"],
    "translation": ["bleu", "comet", "ter"],
}

def rule_gaps(extracted: dict) -> list:
    gaps = []

    metrics = [m.lower() for m in extracted.get("metrics", [])]
    baselines = extracted.get("baselines_or_compared_models", [])
    task = (extracted.get("task") or "").lower()

    if not baselines or len(baselines) == 0:
        gaps.append("No clear baselines / compared models listed.")

    if not metrics or len(metrics) == 0:
        gaps.append("No evaluation metrics clearly reported.")

    if extracted.get("experiments_present") is False:
        gaps.append("Experiments/results section seems missing or unclear.")

    # rough task-metric sanity check
    for t, expected in TASK_METRICS_HINTS.items():
        if t in task:
            if not any(any(e in m for e in expected) for m in metrics):
                gaps.append(f"Metrics may be incomplete for {t} (expected something like {expected}).")
            break

    if extracted.get("ablation_present") is False:
        gaps.append("No ablation study detected (may weaken evidence for component contributions).")

    if extracted.get("robustness_or_safety_eval_present") is False:
        gaps.append("No robustness/safety evaluation detected (may limit real-world reliability).")

    return gaps

def build_gap_prompt(extracted: dict, rule_based_gaps: list) -> str:
    return f"""
You are a research reviewer.
Given the structured extraction and rule-based gaps, output ONLY JSON with:
- gaps: 3 to 6 concise research gaps
- suggested_experiments: 2 to 4 experiments to strengthen the paper
- missing_details_to_check: 2 to 4 things the authors should clarify

Structured extraction:
{json.dumps(extracted, indent=2)}

Rule-based gaps:
{json.dumps(rule_based_gaps, indent=2)}
""".strip()