"""Render explicit semantic choices and check the protected prompt."""

from .common import digest

RULES = {
    "missing_text": {
        "null_or_blank": "Treat NULL and empty or whitespace-only text as missing. For populated text, use NULLIF(BTRIM(column), '') IS NOT NULL.",
        "null_only": "For simpler filters, treat only NULL as missing. Use IS NOT NULL to count populated text, including blank strings.",
    },
    "object_key": {"object_id": "Join museum tables on object_id. Count artworks at the object_id grain; do not multiply counts through expansions."},
    "public_domain": {"explicit_true": "Public domain means is_public_domain IS TRUE. An image URL alone does not establish public-domain status."},
    "ordering": {"question": "Return only requested columns in their requested order. Follow requested sorting and tie breakers; do not add a LIMIT unless requested."},
}


def render(prompt):
    parts = [prompt["instructions"]]
    for key, value in prompt.get("semantics", {}).items():
        try:
            parts.append(RULES[key][value])
        except KeyError:
            raise ValueError(f"Unknown semantic setting: {key}={value}") from None
    return "\n".join(parts)


def protect(prompt, contract):
    errors = [key for key, value in contract["required_semantics"].items()
              if prompt.get("semantics", {}).get(key) != value]
    if digest(prompt["instructions"]) != contract["approved_instructions_sha256"]:
        errors.append("instructions changed; review and update their approved hash")
    if set(prompt.get("semantics", {})) != set(contract["required_semantics"]):
        errors.append("semantic rule set changed")
    if errors:
        raise ValueError("Prompt contract failed: " + "; ".join(errors))
    render(prompt)
    return {"status": "pass", "prompt_sha256": digest(prompt), "contract_sha256": digest(contract)}
