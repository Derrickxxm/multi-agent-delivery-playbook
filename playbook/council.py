"""Validate attribution boundaries and explicit council rulings."""


def validate(record) -> list[str]:
    members = record.get("round1", {})
    positions = record.get("round2_positions", {})
    errors = set()
    if len(members) < 3:
        errors.add("TOO_FEW_MEMBERS")
    if record.get("devils_advocate") not in members:
        errors.add("NO_DEVILS_ADVOCATE")
    if any(member.casefold() in text.casefold() for member in members
           for label, position in positions.items() for text in (label, position)):
        errors.add("NOT_ANONYMIZED")
    if any(not isinstance(item.get("ruling"), str) or not item["ruling"].strip()
           for item in record.get("disagreements", [])):
        errors.add("UNRULED")
    return sorted(errors)
