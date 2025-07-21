import re
import math

# === Constants ===
DEFAULT_VOLTAGE = 230  # volts
WATTS_PER_HP = 746

# === Pattern match helpers ===
def extract_numbers(text):
    return list(map(float, re.findall(r"\d+\.?\d*", text)))

def extract_unit(text, unit_keywords):
    for unit in unit_keywords:
        if unit in text.lower():
            return unit
    return None

# === Compute logic ===
def compute_from_query(question):
    q = question.lower()
    numbers = extract_numbers(q)

    # Exit early if no numbers
    if not numbers:
        return {"type": "none", "result": None}

    voltage = current = power = None
    assume_voltage = False
    notes = []

    # Extract known quantities
    if "volt" in q:
        voltage = numbers[0]
    if "amp" in q:
        current = numbers[-1] if voltage else numbers[0]
    if "watt" in q or "kw" in q:
        power = numbers[0] * 1000 if "kw" in q else numbers[0]

    # --- Case 1: Compute Power from V and I ---
    if voltage and current:
        power_va = voltage * current
        hp = power_va / WATTS_PER_HP
        return {
            "type": "compute_and_query",
            "result": f"Computed Power = {power_va:.2f} VA, ≈ {hp:.2f} HP"
        }

    # --- Case 2: Compute Power with assumed voltage ---
    if current and not voltage:
        voltage = DEFAULT_VOLTAGE
        assume_voltage = True
        power_va = voltage * current
        hp = power_va / WATTS_PER_HP
        return {
            "type": "compute_and_query",
            "result": f"No voltage provided – assuming {voltage}V (single-phase)\nComputed S = V x I = {power_va:.2f} VA ≈ {hp:.2f} HP"
        }

    # --- Case 3: Compute from watts to HP only ---
    if power and ("hp" in q or "horse" in q or "convert" in q):
        hp = power / WATTS_PER_HP
        return {
            "type": "compute_only",
            "result": f"{power:.2f} Watts = {hp:.2f} HP"
        }

    # --- Case 4: HP to Watts ---
    if "hp" in q and not "wire" in q:
        hp_val = numbers[0]
        watts = hp_val * WATTS_PER_HP
        return {
            "type": "compute_only",
            "result": f"{hp_val:.2f} HP = {watts:.2f} Watts"
        }

    return {
        "type": "none",
        "result": None
    }
