# Trabajo Práctico N°13: Gobernanza de Procesos, Automatización y Tríada CIA

## Descripción General
Este proyecto implementa la automatización de procesos de mantenimiento, análisis de seguridad y controles de
acceso bajo la metodología DevSecOps. El objetivo principal es fortalecer la postura de seguridad de la
aplicación Notes App mediante la integración técnica de la **Tríada CIA** (Confidencialidad, Integridad y
Disponibilidad) y el principio de **Privilegio Mínimo**.
---
## Vinculación Técnica con la Tríada CIA

### 1. Disponibilidad (Availability)
* **Control técnico:** Script `scripts/sistema.sh` (Reportes de CPU y Disco).
* **Justificación:** Se implementó un monitoreo preventivo del estado del sistema (`uptime`, `lscpu`, `df -h`)
para garantizar que el servidor cuente con los recursos de cómputo y almacenamiento necesarios para mantener
 la aplicación operativa sin interrupciones.

### 2. Integridad (Integrity)
* **Control técnico:** Script `scripts/sistema.sh` (Backups automatizados con timestamp).
* **Justificación:** Se automatizó el respaldo periódico de la base de datos PostgreSQL (`pg_dump`) garantizando
la consistencia de los datos ante posibles fallos o corrupciones. La política `set -euo pipefail` asegura que el
 script se detenga de inmediato si ocurre un error, evitando la generación de copias incompletas.

### 3. Confidencialidad (Confidentiality)
* **Control técnico:** Restricción de permisos en `/opt/deploy-app/config/app.conf` y segregación de usuarios.
* **Justificación:** Se asignaron permisos estricto `600` al archivo de configuración sensible para asegurar que
únicamente el usuario propietario pueda leerlo. Se configuró el usuario de sistema no privilegiado `devops-deploy`
perteneciente al grupo `deploy-team` para evitar la ejecución de despliegues bajo la cuenta `root`.
---
## Análisis de Seguridad Manual (Black Box)
* **Herramienta:** OWASP ZAP (Zaproxy 2.17.0).
* **Enfoque:** Se realizó un escaneo inicial en modo de exploración manual contra la aplicación en ejecución local
para identificar vulnerabilidades de aplicación web y errores de configuración en la capa pública antes de avanzar
en la automatización del pipeline.
---
## Validación y Auditoría
El script `scripts/verificar-permisos.sh` actúa como una puerta de calidad (Quality Gate) que valida
automáticamente en cada ejecución:
1. Existencia y tamaño del backup base (`notes_db.sql`).
2. Propietario (`devops-deploy`), grupo (`deploy-team`) y permisos exactos (`600`) del archivo de configuración.

