# Trabajo Práctico N°13: DevSecOps — DAST Automatizado con OWASP ZAP y GitHub Actions

## Descripción General
Este proyecto implementa la automatización de análisis de seguridad dinámico (DAST), monitoreo de infraestructura y controles de 
acceso bajo la metodología DevSecOps. El objetivo principal es fortalecer la postura de seguridad de la **Notes App** mediante 
la integración de OWASP ZAP en el pipeline de CI/CD (GitHub Actions) y el cumplimiento de la Tríada CIA (Confidencialidad, 
Integridad y Disponibilidad).

---

## 🔒 Vinculación Técnica con la Tríada CIA

### 1. Disponibilidad (Availability)
* **Control técnico:** Script `scripts/sistema.sh` (Reportes de CPU y Disco).
* **Justificación:** Monitoreo preventivo del estado del sistema (`uptime`, `lscpu`, `df -h`) para garantizar la operatividad
 continua del servidor.

### 2. Integridad (Integrity)
* **Control técnico:** Respaldo automatizado de base de datos y política `set -euo pipefail`.
* **Justificación:** Automatización de backups de PostgreSQL (`pg_dump`). El control de fallos estricto evita respaldos corruptos
 o incompletos.

### 3. Confidencialidad (Confidentiality)
* **Control técnico:** Permisos estrictos (`600`), usuario `devops-deploy` y gestión de **GitHub Secrets**.
* **Justificación:** Segregación de privilegios para evitar despliegues como `root`. Además, las credenciales de prueba
 (`APP_USER`, `APP_PASSWORD`) se inyectan dinámicamente al contenedor de ZAP en GitHub Actions sin exponerlas en el código fuente.

---

## 🛡️ Análisis de Seguridad Dinámico (DAST) con OWASP ZAP

### 1. Escaneo Automatizado en Pipeline (Automation Framework)
Se integró OWASP ZAP mediante su **Automation Framework (AF)** en el workflow `.github/workflows/zap-security.yml`. Ante cada
 `push` o `pull_request` en la rama `main`:
1. GitHub Actions levanta la Notes App usando `docker compose up -d`.
2. ZAP ejecuta el plan `.zap/zap-plan.yml` que incluye:
   * **Spider & SpiderAjax:** Descubrimiento de rutas y endpoints de la aplicación.
   * **Passive Scan:** Verificación pasiva de cabeceras de seguridad y vulnerabilidades conocidas.
   * **Active Scan:** Ataques dinámicos (Fuzzing, SQL Injection, XSS) sobre los endpoints detectados.
3. Se genera un reporte estético en HTML guardado como artefacto del pipeline (`zap-security-report`).

---

## 🛠️ Archivos del Proyecto y Estructura

* `.zap/zap-plan.yml`: Definición declarativa de las fases de escaneo de OWASP ZAP.
* `.github/workflows/zap-security.yml`: Workflow de GitHub Actions para la ejecución automatizada de DAST.
* `verificar-zap.sh`: Script local para validar la sintaxis del plan de ZAP en Docker antes de subir cambios.
* `scripts/sistema.sh`: Script de mantenimiento y monitoreo de la infraestructura.
* `scripts/verificar-permisos.sh`: Auditoría de calidad (*Quality Gate*) de controles CIA.

---

## 🚀 Verificación Local y Ejecución

Para validar la sintaxis del plan de ZAP localmente antes de realizar un commit:

```bash
chmod +x verificar-zap.sh
./verificar-zap.sh
