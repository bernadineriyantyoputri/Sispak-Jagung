from typing import Dict, List

# ============================================================
# COMBINE CF
# ============================================================
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


# ============================================================
# HITUNG 1 RULE
# ============================================================
def evaluate_rule(rule: Dict, inputs: Dict[str, float]) -> (float, Dict[str, float]):
    combined = None
    cond_evidence = {}

    for cond in rule.get("conditions", []):
        sym = cond["symptom"]
        weight = float(cond.get("weight", 1.0))
        user_val = float(inputs.get(sym, 0.0))

        evidence = user_val * weight
        cond_evidence[sym] = evidence

        if combined is None:
            combined = evidence
        else:
            combined = combine_cf(combined, evidence)

    if combined is None:
        combined = 0.0

    final = combined * float(rule.get("rule_cf", 1.0))
    final = max(-1, min(1, round(final, 4)))

    return final, cond_evidence


# ============================================================
# FORWARD CHAIN – FINAL STAGE
# ============================================================
def forward_chain(rules: List[Dict], inputs: Dict[str, float]):
    hasil = []

    for rule in rules:
        final, cond_evidence = evaluate_rule(rule, inputs)
        hasil.append({
            "id": rule["id"],
            "name": rule["name"],
            "name_id": rule.get("name_id", ""),
            "description": rule["description"],
            "cf": final,
            "conditions_evidence": cond_evidence
        })

    hasil = [h for h in hasil if h["cf"] > 0]
    hasil.sort(key=lambda x: x["cf"], reverse=True)
    return hasil


# ============================================================
# TAHAP 1 — SCREENING AWAL
# ============================================================
def forward_screening(rules: List[Dict], inputs: Dict[str, float], threshold: float = 0.05):
    candidates = []
    for rule in rules:
        final, _ = evaluate_rule(rule, inputs)
        if final >= threshold:
            candidates.append(rule["id"])
    return candidates


# ============================================================
# TAHAP 2 — FILTER GEJALA KONFIRMASI KHUSUS
# ============================================================
def get_confirmation_symptoms(candidate_ids, symptoms_all, rules):
    """
    Ambil gejala dari rules yang termasuk kandidat.
    """
    symptom_set = set()

    for rule in rules:
        if rule["id"] in candidate_ids:
            for c in rule.get("conditions", []):
                symptom_set.add(c["symptom"])

    # Hanya ambil gejala yang ada dalam database symptoms
    filtered = {sym: symptoms_all.get(sym) for sym in symptom_set if sym in symptoms_all}
    return filtered



# ============================================================
# TAHAP 3 — DUMMY MODEL (JIKA ADA GAMBAR)
# ============================================================
def predict_image_stub(image):
    """
    Stub model prediksi gambar, hanya contoh.
    """
    return {
        "busuk": 0.0,
        "karat": 0.0,
        "hawar": 0.0
    }
