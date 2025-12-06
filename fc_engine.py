from typing import Dict, List
import json, os

def combine_cf(cf1: float, cf2: float) -> float:
    if cf1 is None:
        return cf2
    if cf2 is None:
        return cf1
    if cf1 >= 0 and cf2 >= 0:
        return cf1 + cf2 * (1 - cf1)
    if cf1 <= 0 and cf2 <= 0:
        return cf1 + cf2 * (1 + cf1)
    denom = 1 - min(abs(cf1), abs(cf2))
    if denom == 0:
        return 0.0
    return (cf1 + cf2) / denom

def evaluate_rule(rule: Dict, inputs: Dict[str, float]) -> float:
    combined = None
    for cond in rule.get("conditions", []):
        s_key = cond["symptom"]
        weight = float(cond.get("weight", 1.0))
        val = float(inputs.get(s_key, 0.0))
        evidence = val * weight
        if combined is None:
            combined = evidence
        else:
            combined = combine_cf(combined, evidence)

    if combined is None:
        combined = 0.0

    rule_cf = float(rule.get("rule_cf", 1.0))
    final = combined * rule_cf

    if final > 1: final = 1.0
    if final < -1: final = -1.0
    return float(final)

def forward_chain(rules: List[Dict], inputs: Dict[str, float]) -> List[Dict]:
    results = []

    for r in rules:
        conds_evidence = {}
        for cond in r.get("conditions", []):
            s = cond["symptom"]
            w = float(cond.get("weight", 1.0))
            v = float(inputs.get(s, 0.0))
            conds_evidence[s] = round(v * w, 4)

        cf = evaluate_rule(r, inputs)

        results.append({
            "id": r["id"],
            "name": r["name"],
            "description": r.get("description",""),
            "cf": round(cf, 4),
            "conditions_evidence": conds_evidence,
            "rule_cf": float(r.get("rule_cf", 1.0))
        })

    results = [r for r in results if r["cf"] > 0]

    results.sort(key=lambda x: x["cf"], reverse=True)

    return results
