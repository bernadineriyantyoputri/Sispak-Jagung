from typing import Dict, List, Tuple


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


def evaluate_rule(rule: Dict, inputs: Dict[str, float]) -> Tuple[float, Dict[str, float]]:
    combined = None
    cond_evidence = {}

    for cond in rule.get("conditions", []):
        symptom = cond["symptom"]
        weight = float(cond.get("weight", 1.0))
        user_val = float(inputs.get(symptom, 0.0))  # 0–1

        evidence = user_val * weight
        cond_evidence[symptom] = round(evidence, 4)

        combined = evidence if combined is None else combine_cf(combined, evidence)

    if combined is None:
        combined = 0.0

    final_cf = combined * float(rule.get("rule_cf", 1.0))
    final_cf = max(-1, min(1, round(final_cf, 4)))

    return final_cf, cond_evidence


def forward_chain(rules: List[Dict], inputs: Dict[str, float]) -> List[Dict]:
    results = []

    for rule in rules:
        final_cf, evidence = evaluate_rule(rule, inputs)
        results.append({
            "id": rule["id"],
            "name": rule["name"],
            "name_id": rule.get("name_id", ""),
            "description": rule["description"],
            "cf": final_cf,
            "conditions_evidence": evidence
        })

    results = [r for r in results if r["cf"] > 0]
    results.sort(key=lambda x: x["cf"], reverse=True)
    return results


def forward_screening(
    rules: List[Dict],
    inputs: Dict[str, float],
    threshold: float = 0.05
) -> List[str]:
    candidates = []

    for rule in rules:
        final_cf, _ = evaluate_rule(rule, inputs)
        if final_cf >= threshold:
            candidates.append(rule["id"])

    return candidates


def get_confirmation_symptoms(candidate_ids, symptoms_all, rules):
    symptom_set = set()

    for rule in rules:
        if rule["id"] in candidate_ids:
            for cond in rule.get("conditions", []):
                symptom_set.add(cond["symptom"])

    return {
        sym: symptoms_all[sym]
        for sym in symptom_set
        if sym in symptoms_all
    }


def predict_image_stub(image):
    return {
        "busuk": 0.0,
        "karat": 0.0,
        "hawar": 0.0
    }
