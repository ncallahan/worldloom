from typing import Any

def anomaly(kind: str, path: str, position: int, value: Any) -> dict[str, Any]:
    return {"kind": kind, "path": path, "position": position, "value": sanitize_without_anomalies(value)}


def sanitize_string(value: str) -> tuple[str, list[str]]:
    """Tolerate lone surrogates at the FMG importer boundary only."""
    result: list[str] = []
    labels: list[str] = []
    index = 0
    while index < len(value):
        code = ord(value[index])
        if 0xD800 <= code <= 0xDFFF:
            if (
                0xD800 <= code <= 0xDBFF
                and index + 1 < len(value)
                and 0xDC00 <= ord(value[index + 1]) <= 0xDFFF
            ):
                result.extend((value[index], value[index + 1]))
                index += 2
                continue
            result.append("\ufffd")
            labels.append(f"U+{code:04X}")
        else:
            result.append(value[index])
        index += 1
    return "".join(result), labels


def sanitize_without_anomalies(value: Any) -> Any:
    """Sanitize a copied value without recording anomalies for the copy."""
    return sanitize_strings(value, "", -1, [])


def sanitize_strings(
    value: Any,
    path: str,
    position: int,
    anomalies: list[dict[str, Any]],
) -> Any:
    """Recursively sanitize strings; this does not define core string validity."""
    if isinstance(value, str):
        sanitized, labels = sanitize_string(value)
        if labels:
            anomalies.append(anomaly("lone-surrogate", path, position, labels))
        return sanitized
    if isinstance(value, list):
        return [
            sanitize_strings(item, f"{path}[{index}]", position, anomalies)
            for index, item in enumerate(value)
        ]
    if isinstance(value, dict):
        sanitized_dict: dict[Any, Any] = {}
        for key, item in value.items():
            key_path = f"{path}.{{key}}"
            if isinstance(key, str):
                sanitized_key, labels = sanitize_string(key)
                if labels:
                    anomalies.append(anomaly("lone-surrogate", key_path, position, labels))
                key = sanitized_key
            if key in sanitized_dict:
                raise ValueError(f"Sanitized dict key collision at {path}: {key!r}")
            sanitized_dict[key] = sanitize_strings(
                item, f"{path}.{key}", position, anomalies
            )
        return sanitized_dict
    return value



def anomaly_report(anomalies: list[dict[str, Any]]) -> dict[str, Any]:
    """Build the stable report shared by FMG importer anomaly collections."""
    counts: dict[str, dict[str, int]] = {}
    for item in anomalies:
        kind_counts = counts.setdefault(item["kind"], {})
        kind_counts[item["path"]] = kind_counts.get(item["path"], 0) + 1
    examples = sorted(
        anomalies,
        key=lambda item: (
            item["path"],
            item["position"],
            item["kind"],
            repr(item["value"]),
        ),
    )[:20]
    return {"counts": counts, "examples": examples, "total": len(anomalies)}
