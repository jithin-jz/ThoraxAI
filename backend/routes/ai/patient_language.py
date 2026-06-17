"""
patient_language.py
===================
Plain-English explanations for every body part + condition.
Written at a 6th-grade reading level — no medical jargon.

Each entry has:
  headline      – one-line summary (shown large)
  what_found    – what the AI saw in simple words
  what_it_means – what it means for your health
  what_to_do    – action the patient should take
  urgency       – "good" | "watch" | "soon" | "urgent"
  emoji         – visual indicator
"""

# ── Normal / Healthy fallback (used by all body parts) ───────────────────────

_NORMAL_TEMPLATE = {
    "headline": "Your {part} looks healthy",
    "what_found": (
        "The AI did not find any signs of disease or injury in your {part} X-ray. "
        "Everything appears to be within normal limits."
    ),
    "what_it_means": ("Based on this X-ray, your {part} looks healthy. " "That is great news!"),
    "what_to_do": (
        "No urgent action is needed. Keep up with your regular health check-ups "
        "and let your doctor know if you develop any new symptoms."
    ),
    "urgency": "good",
    "emoji": "✅",
}

# ── Condition-specific plain-English templates ────────────────────────────────

PATIENT_LANGUAGE: dict[str, dict[str, dict]] = {
    # ── CHEST ─────────────────────────────────────────────────────────────────
    "chest": {
        "Normal": {
            **_NORMAL_TEMPLATE,
            "headline": "Your lungs look healthy",
            "what_found": (
                "The AI did not find any signs of infection, fluid, or disease "
                "in your chest X-ray."
            ),
            "what_it_means": "Your lungs and heart appear to be in good shape.",
        },
        "Pneumonia": {
            "headline": "Possible lung infection detected",
            "what_found": (
                "The AI found patterns in your chest X-ray that look like "
                "pneumonia — an infection that causes the air sacs in your "
                "lungs to fill with fluid or pus."
            ),
            "what_it_means": (
                "Pneumonia can make breathing difficult and cause fever, cough, "
                "and chest pain. It usually needs treatment with medicine. "
                "The good news is that it is very treatable, especially when "
                "caught early."
            ),
            "what_to_do": (
                "Please see a doctor as soon as possible — ideally today or "
                "tomorrow. Your doctor will confirm the diagnosis and prescribe "
                "the right treatment, usually antibiotics or antiviral medicine."
            ),
            "urgency": "urgent",
            "emoji": "⚠️",
        },
    },
}


def get_patient_summary(body_part: str, prediction: str, confidence: float) -> dict:
    """
    Returns a plain-English patient summary for a given AI result.

    Args:
        body_part:  e.g. "chest", "knee"
        prediction: e.g. "Pneumonia", "Normal"
        confidence: float 0-1

    Returns dict with: headline, what_found, what_it_means, what_to_do, urgency, emoji,
                        confidence_text, body_part
    """
    part_templates = PATIENT_LANGUAGE.get(body_part, {})

    # Find matching condition (case-insensitive, partial match)
    template = None
    for cond, tmpl in part_templates.items():
        if cond.lower() == prediction.lower():
            template = tmpl
            break

    # If not found, use Normal fallback
    if template is None:
        if prediction.lower() == "normal":
            template = {**_NORMAL_TEMPLATE}
        else:
            # Unknown condition — generic warning
            template = {
                "headline": f"Something was detected in your {body_part.replace('_', ' ')}",
                "what_found": (
                    f"The AI detected {prediction} in your " f"{body_part.replace('_', ' ')} X-ray."
                ),
                "what_it_means": (
                    "Please discuss this result with your doctor for a " "full explanation."
                ),
                "what_to_do": "Book an appointment with your doctor soon.",
                "urgency": "soon",
                "emoji": "⚠️",
            }

    # Fill in {part} placeholders
    part_label = body_part.replace("_", " ")
    result = {
        k: (v.format(part=part_label) if isinstance(v, str) else v) for k, v in template.items()
    }

    # Confidence in plain English
    pct = round(confidence * 100)
    if pct >= 90:
        conf_text = f"The AI is very confident in this result ({pct}%)."
    elif pct >= 75:
        conf_text = (
            f"The AI is fairly confident in this result ({pct}%). Your doctor should confirm."
        )
    else:
        conf_text = f"The AI is less certain about this result ({pct}%). A doctor's review is especially important."

    result["confidence_text"] = conf_text
    result["body_part_label"] = part_label.title()
    result["prediction"] = prediction

    return result
