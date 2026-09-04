import json
import os
import re
from pathlib import Path

sarif_path = Path("reports/zap-report-ci.sarif.json")

if not sarif_path.exists():
    raise SystemExit(f"No existe {sarif_path}")

secret = os.environ.get("ZAP_APP_PASSWORD", "")

with sarif_path.open("r", encoding="utf-8") as f:
    data = json.load(f)


def redact(value):
    if not isinstance(value, str):
        return value

    # Ocultar el secreto real donde aparezca.
    if secret:
        value = value.replace(secret, "***REDACTED***")

    # Ocultar passwords aunque no coincidan con la variable.
    value = re.sub(
        r'(\\"password\\":\\")[^"\\]*(\\")',
        r'\1***REDACTED***\2',
        value,
        flags=re.IGNORECASE,
    )

    value = re.sub(
        r'("password"\s*:\s*")[^"]*(")',
        r'\1***REDACTED***\2',
        value,
        flags=re.IGNORECASE,
    )

    return value


def sanitize_strings(obj):
    if isinstance(obj, dict):
        return {key: sanitize_strings(value) for key, value in obj.items()}

    if isinstance(obj, list):
        return [sanitize_strings(value) for value in obj]

    if isinstance(obj, str):
        return redact(obj)

    return obj


def get_target(result):
    """
    Recupera la URL atacada antes de eliminar webRequest/webResponse.
    """
    web_request = result.get("webRequest")

    if isinstance(web_request, dict):
        target = web_request.get("target")
        if isinstance(target, str):
            return target

    message = result.get("message", {}).get("text", "")
    match = re.search(r"Target URL:\s*([^\s|]+)", message)

    if match:
        return match.group(1)

    return "http://localhost"


def repo_file_for_target(target):
    """
    Asocia el hallazgo a un archivo real del repositorio.
    """
    if "/api/" in target:
        return "backend/app.py"

    return "frontend/index.html"


def sanitize_result(result):
    target = get_target(result)

    # Conservar el contexto web de forma segura en el mensaje,
    # pero sin webRequest/webResponse.
    message = result.setdefault("message", {})
    text = message.get("text", "")

    if target and target not in text:
        message["text"] = f"Target URL: {target} | {text}"

    # Crear una ubicación válida para GitHub Code Scanning.
    artifact = repo_file_for_target(target)

    result["locations"] = [
        {
            "physicalLocation": {
                "artifactLocation": {
                    "uri": artifact
                },
                "region": {
                    "startLine": 1,
                    "startColumn": 1
                }
            }
        }
    ]

    # Eliminar extensiones propias de ZAP que contienen URLs HTTP
    # y que GitHub no necesita para Code Scanning.
    result.pop("webRequest", None)
    result.pop("webResponse", None)

    # Eliminar ubicaciones secundarias que podrían contener URLs HTTP.
    result.pop("relatedLocations", None)
    result.pop("codeFlows", None)

    # Limpiar fingerprints.
    partial = result.get("partialFingerprints")
    if isinstance(partial, dict):
        for key, value in partial.items():
            partial[key] = redact(value)

    return result


# Sanitizar strings generales primero.
data = sanitize_strings(data)

# Procesar resultados.
for run in data.get("runs", []):
    for result in run.get("results", []):
        sanitize_result(result)

    # Eliminar referencias de artifacts que puedan contener URLs.
    artifacts = run.get("artifacts")
    if isinstance(artifacts, list):
        for artifact in artifacts:
            if isinstance(artifact, dict):
                location = artifact.get("location")
                if isinstance(location, dict):
                    uri = location.get("uri")
                    if isinstance(uri, str) and uri.startswith(
                        ("http://", "https://")
                    ):
                        artifact.pop("location", None)

    # Eliminar referencias externas de reglas que no son necesarias.
    tool = run.get("tool", {})
    driver = tool.get("driver", {}) if isinstance(tool, dict) else {}

    if isinstance(driver, dict):
        driver.pop("informationUri", None)
        driver.pop("downloadUri", None)

        rules = driver.get("rules", [])
        if isinstance(rules, list):
            for rule in rules:
                if isinstance(rule, dict):
                    rule.pop("helpUri", None)


with sarif_path.open("w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"SARIF sanitizado: {sarif_path}")
