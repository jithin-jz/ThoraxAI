"""
Body Part Registry — defines every supported X-ray scan type
and the medical conditions the AI can detect for each.

Each body part has:
  - label         : human-readable display name
  - conditions    : ordered list of class names the model predicts
                    (index 0 = normal/no finding baseline)
  - model_file    : filename of the fine-tuned model weights for this part
                    (placed in backend/routes/ai/models/)
  - description   : what the AI looks for

Adding a new body part:
  1. Add an entry here.
  2. Train/obtain a model checkpoint → save as models/<model_file>.
  3. The registry auto-registers it — no other code changes needed.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class BodyPartConfig:
    label: str
    conditions: tuple[str, ...]  # frozen-safe (immutable sequence)
    model_file: str
    description: str


# ── Registry ──────────────────────────────────────────────────────────────────
_REGISTRY: dict[str, BodyPartConfig] = {
    # ── Chest ──────────────────────────────────────────────────────────────
    "chest": BodyPartConfig(
        label="Chest / Thorax",
        conditions=("Normal", "Pneumonia"),
        model_file="chest.pth",
        description=(
            "Analyzes lung fields, heart silhouette, and pleural spaces. "
            "Detects pneumonia, pleural effusion, and cardiomegaly."
        ),
    ),
}


def get_body_part(key: str) -> BodyPartConfig:
    """
    Retrieve config for a body part by its key.
    Raises KeyError with a helpful message if not found.
    """
    key = key.lower().strip()
    if key not in _REGISTRY:
        valid = ", ".join(sorted(_REGISTRY.keys()))
        raise KeyError(f"Unknown body part '{key}'. " f"Supported values: {valid}")
    return _REGISTRY[key]


def list_body_parts() -> dict[str, dict]:
    """Return all supported body parts as a JSON-serializable dict."""
    return {
        key: {
            "label": cfg.label,
            "conditions": cfg.conditions,
            "description": cfg.description,
        }
        for key, cfg in _REGISTRY.items()
    }


# All valid body part keys — useful for Pydantic validation
VALID_BODY_PARTS = list(_REGISTRY.keys())
