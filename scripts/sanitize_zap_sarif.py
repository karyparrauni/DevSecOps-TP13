import json
import os
from pathlib import Path

sarif_path = Path("reports/zap-report-ci.sarif.json")

if not sarif_path.exists():
    raise SystemExit(f"No existe {sarif_path}")

secret = os.environ.get("ZAP_APP_PASSWORD", "")

with sarif_path.open("r", encoding="utf-8") as f:
    data = json.load(f)


def sanitize(value):
    if isinstance(value, dict):
        cleaned = {}

        for key, item in value.items():

            # Estas extensiones de ZAP contienen las URLs HTTP
            # que GitHub Code Scanning intenta interpretar como
            # ubicaciones de archivos.
            if key in ("webRequest", "webResponse"):
                continue

            # Eliminar cualquier URI absoluta HTTP/HTTPS.
            if (
                key == "uri"
                and isinstance(item, str)
                and item.startswith(("http://", "https://"))
            ):
                continue

            cleaned[key] = sanitize(item)

        return cleaned

    if isinstance(value, list):
        return [sanitize(item) for item in value]

    if isinstance(value, str):
        # Eliminar el secreto real de cualquier texto.
        if secret:
            value = value.replace(secret, "***REDACTED***")

        return value

    return value


data = sanitize(data)

with sarif_path.open("w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"SARIF sanitizado: {sarif_path}")
