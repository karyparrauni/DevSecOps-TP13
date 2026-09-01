x# Trabajo Práctico N°13: DevSecOps — DAST Automatizado con OWASP ZAP y GitHub Actions

## Descripción General

Este proyecto implementa prácticas de **DevSecOps** sobre la **Notes App**, integrando controles de disponibilidad,
integridad y confidencialidad junto con un proceso automatizado de **Dynamic Application Security Testing (DAST)**
 mediante **OWASP ZAP**.

El objetivo principal del trabajo es incorporar la seguridad dentro del ciclo de integración continua, de manera
que cada cambio enviado al repositorio pueda ser evaluado automáticamente mediante un análisis de seguridad de la
aplicación en ejecución.

La solución integra:

* Notes App ejecutada mediante Docker Compose.
* Backend Flask.
* Frontend servido mediante Nginx.
* PostgreSQL como base de datos.
* Autenticación básica mediante usuario, contraseña y token Bearer.
* GitHub Secrets para proteger credenciales.
* OWASP ZAP Automation Framework.
* Spider y Ajax Spider.
* Passive Scan.
* Active Scan.
* Generación automática de reportes.
* GitHub Actions.
* Artifact de los resultados del análisis.

---

# 🔒 Vinculación Técnica con la Tríada CIA

## 1. Disponibilidad (Availability)

**Control técnico:** `scripts/sistema.sh`

El script permite realizar verificaciones del estado del sistema y generar reportes de recursos.

Entre los controles utilizados se encuentran:

```bash
uptime
lscpu
df -h
```

Estos comandos permiten observar información relacionada con el tiempo de actividad, características del sistema
y disponibilidad de espacio en disco.

El objetivo es detectar preventivamente situaciones que puedan afectar la continuidad de los servicios.

---

## 2. Integridad (Integrity)

**Controles técnicos:**

* Respaldo automatizado de PostgreSQL.
* Uso de `pg_dump`.
* Scripts Bash con `set -euo pipefail`.
* Control de cambios mediante Git.

El respaldo de la base de datos permite disponer de una copia recuperable de la información.

El uso de:

```bash
set -euo pipefail
```

permite que los scripts fallen ante errores, variables no definidas o errores dentro de pipelines de comandos,
reduciendo el riesgo de generar operaciones incompletas o resultados inconsistentes.

Además, Git permite registrar y controlar los cambios realizados sobre la aplicación, configuraciones y pipeline.

---

## 3. Confidencialidad (Confidentiality)

**Controles técnicos:**

* Variables de entorno.
* Archivo `.env` excluido mediante `.gitignore`.
* GitHub Secrets.
* Usuario no privilegiado para ejecutar el backend.
* Autenticación mediante usuario, contraseña y token Bearer.
* Protección de endpoints de notas.

Las credenciales de la aplicación se manejan mediante:

```text
APP_USER
APP_PASSWORD
```

El archivo `.env` se encuentra excluido del control de versiones:

```gitignore
.env
```

La verificación se realizó mediante:

```bash
git check-ignore -v .env
```

y:

```bash
git ls-files .env
```

Este último no debe devolver resultados, confirmando que `.env` no está versionado.

En GitHub Actions, las credenciales se obtienen mediante:

```yaml
${{ secrets.APP_USER }}
${{ secrets.APP_PASSWORD }}
```

evitando escribir directamente las credenciales en el workflow.

---

# 🔐 Autenticación de la Notes App

Como parte del TP13B se incorporó un mecanismo básico de autenticación.

El backend utiliza las variables:

```python
APP_USER = os.getenv("APP_USER", "")
APP_PASSWORD = os.getenv("APP_PASSWORD", "")
```

La autenticación se realiza mediante:

```text
POST /api/login
```

El cliente envía:

```json
{
  "username": "...",
  "password": "..."
}
```

Cuando las credenciales son válidas, el backend genera un token de sesión.

Las operaciones sobre las notas requieren:

```http
Authorization: Bearer <TOKEN>
```

Los endpoints protegidos son:

```text
GET    /api/notes
GET    /api/notes/<id>
POST   /api/notes
DELETE /api/notes/<id>
```

El endpoint:

```text
GET /health
```

permanece disponible sin autenticación para permitir las comprobaciones de estado de la aplicación.

---

## Verificación de la autenticación

El acceso sin token devuelve:

```text
HTTP/1.1 401 UNAUTHORIZED
```

con una respuesta similar a:

```json
{
  "error": "autenticación requerida"
}
```

Luego se obtiene un token mediante:

```bash
curl -i -X POST http://localhost/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"devops-zap"}'
```

El acceso autenticado se comprueba mediante:

```bash
curl -i http://localhost/api/notes \
  -H "Authorization: Bearer $TOKEN"
```

obteniendo:

```text
HTTP/1.1 200 OK
```

---

# 🐳 Arquitectura con Docker Compose

La aplicación se compone de tres servicios principales:

```text
               Notes App
                   │
        ┌──────────┴──────────┐
        │                     │
     Frontend               Backend
      Nginx                  Flask
        │                     │
        └──────────┬──────────┘
                   │
              PostgreSQL
```

Los servicios son:

```text
db
backend
frontend
```

El estado de los contenedores puede verificarse con:

```bash
docker compose ps
```

La aplicación se levanta mediante:

```bash
docker compose up -d
```

y puede detenerse mediante:

```bash
docker compose down
```

Cuando se modifica una imagen:

```bash
docker compose up -d --build
```

---

# 🛡️ Análisis de Seguridad Dinámico (DAST) con OWASP ZAP

## Automation Framework

Se integró **OWASP ZAP Automation Framework (AF)** utilizando el archivo:

```text
.zap/zap-plan.yml
```

El plan define de manera declarativa las tareas que ZAP debe ejecutar.

El contexto utilizado es:

```text
notes-app-context
```

y el objetivo de análisis es:

```text
http://localhost
```

---

## Fases del análisis

### 1. Spider

```yaml
- type: spider
```

El Spider realiza el descubrimiento tradicional de recursos y rutas de la aplicación.

Durante las pruebas se detectaron:

```text
4 URLs
```

---

### 2. Ajax Spider

```yaml
- type: spiderAjax
```

Permite descubrir recursos relacionados con contenido dinámico y JavaScript.

Durante las pruebas también se detectaron recursos adicionales de la aplicación.

---

### 3. Passive Scan

```yaml
- type: passiveScan-wait
```

Esta fase permite completar el procesamiento pasivo de las solicitudes obtenidas durante el descubrimiento.

El análisis pasivo permite identificar problemas que pueden observarse sin realizar ataques activos sobre
la aplicación.

---

### 4. Active Scan

```yaml
- type: activeScan
```

Es la fase de DAST activo.

Se configuró utilizando:

```yaml
user: zap-user
policy: Default Policy
maxScanDurationInMins: 5
```

Esto permite realizar pruebas activas sobre la aplicación utilizando un usuario autenticado.

El Active Scan puede detectar distintos problemas de seguridad relacionados con entradas y respuestas de la
aplicación.

---

# 🔑 Autenticación de ZAP

El Automation Framework fue configurado para utilizar el endpoint:

```text
POST /api/login
```

mediante autenticación JSON.

El cuerpo de la solicitud se define como:

```yaml
loginRequestBody: '{"username":"${ZAP_APP_USER}","password":"${ZAP_APP_PASSWORD}"}'
```

Las credenciales son recibidas mediante variables de entorno:

```text
ZAP_APP_USER
ZAP_APP_PASSWORD
```

El usuario utilizado por el Active Scan es:

```text
zap-user
```

De esta manera, ZAP puede realizar análisis sobre recursos protegidos y no solamente sobre la superficie pública
de la aplicación.

---

# 🔐 GitHub Secrets

En el repositorio se configuraron los siguientes **Repository Secrets**:

```text
APP_USER
APP_PASSWORD
```

El workflow los utiliza mediante:

```yaml
APP_USER: ${{ secrets.APP_USER }}
APP_PASSWORD: ${{ secrets.APP_PASSWORD }}
```

Para ZAP:

```yaml
ZAP_APP_USER: ${{ secrets.APP_USER }}
ZAP_APP_PASSWORD: ${{ secrets.APP_PASSWORD }}
```

El uso de Secrets evita almacenar las credenciales directamente en el repositorio.

---

# ⚙️ GitHub Actions

El pipeline se encuentra definido en:

```text
.github/workflows/zap-security.yml
```

Se ejecuta ante:

```yaml
push:
  branches: [ main, develop ]

pull_request:
  branches: [ main ]
```

El flujo es:

```text
Push / Pull Request
        ↓
Checkout
        ↓
Docker Compose
        ↓
Levantar Notes App
        ↓
Preparar reports/
        ↓
OWASP ZAP
        ↓
Spider
        ↓
Ajax Spider
        ↓
Passive Scan
        ↓
Active Scan
        ↓
Generar reporte
        ↓
Upload Artifact
```

---

# 📄 Generación de reportes

El plan de ZAP genera un reporte mediante:

```yaml
- type: report
```

utilizando el template:

```text
modern
```

En GitHub Actions se genera el reporte dentro del directorio de trabajo de ZAP:

```text
/zap/wrk/reports
```

El reporte se conserva como Artifact mediante:

```yaml
uses: actions/upload-artifact@v4
```

La configuración utilizada es:

```yaml
with:
  name: zap-security-report
  path: reports/
  retention-days: 7
```

Por lo tanto, el resultado puede consultarse desde la ejecución correspondiente de GitHub Actions.

---

# 🧪 Verificación local

Antes de utilizar GitHub Actions se realizaron pruebas locales para comprobar el funcionamiento del Automation
Framework.

## Ejecutar ZAP instalado localmente

```bash
/home/alumno/.local/opt/ZAP_2.17.0/zap.sh \
  -cmd \
  -autorun /home/alumno/DevSecOps/.zap/zap-plan.yml
```

Este comando ejecuta ZAP en modo línea de comandos y utiliza automáticamente el plan indicado.

---

## Ejecutar ZAP mediante Docker

Para reproducir el entorno que posteriormente utiliza GitHub Actions se utilizó:

```bash
docker run --rm \
  -e ZAP_APP_USER \
  -e ZAP_APP_PASSWORD \
  -v "$(pwd):/zap/wrk/:rw" \
  ghcr.io/zaproxy/zaproxy:stable \
  zap.sh -cmd -autorun /zap/wrk/.zap/zap-plan.yml
```

La ejecución finalizó correctamente con:

```text
Automation plan succeeded!
```

---

# 🔍 Comandos principales utilizados

## Docker

### Ver contenedores

```bash
docker compose ps
```

Muestra los servicios, estados y puertos publicados.

### Levantar servicios

```bash
docker compose up -d
```

Inicia los servicios en segundo plano.

### Reconstruir imágenes

```bash
docker compose up -d --build
```

Reconstruye las imágenes antes de iniciar los servicios.

### Detener servicios

```bash
docker compose down
```

Detiene y elimina los contenedores y la red creada por Compose.

### Ver logs

```bash
docker compose logs backend --tail=50
```

Muestra los últimos mensajes del backend.

---

# 🌐 Comandos HTTP

### Comprobar aplicación

```bash
curl -i http://localhost
```

Comprueba si el frontend responde.

### Comprobar estado del backend

```bash
curl -i http://localhost/health
```

Permite verificar conectividad con PostgreSQL.

### Autenticarse

```bash
curl -i -X POST http://localhost/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"devops-zap"}'
```

Realiza el login y obtiene un token.

### Consultar notas

```bash
curl -i http://localhost/api/notes \
  -H "Authorization: Bearer $TOKEN"
```

Realiza una petición autenticada.

---

# 🔧 Comandos de inspección

### Ver archivos del proyecto

```bash
find . -maxdepth 3 -type f | sort
```

### Mostrar configuración

```bash
cat docker-compose.yml
cat .zap/zap-plan.yml
cat .github/workflows/zap-security.yml
```

### Buscar variables de autenticación

```bash
grep -nE 'APP_USER|APP_PASSWORD' backend/app.py docker-compose.yml
```

### Buscar configuración de ZAP

```bash
grep -nE 'urls:|includePaths:|loginPageUrl|loginRequestUrl' .zap/zap-plan.yml
```

### Comprobar procesos Gunicorn

```bash
docker compose exec backend ps aux | grep gunicorn
```

---

# 🌿 Comandos Git utilizados

### Ver estado

```bash
git status --short
```

Muestra archivos modificados, eliminados o no versionados.

### Preparar cambios

```bash
git add archivo
```

Agrega un archivo al área de staging.

### Crear commit

```bash
git commit -m "mensaje"
```

Registra los cambios en el historial.

### Ver último commit

```bash
git show --stat --oneline HEAD
```

Muestra el commit más reciente y un resumen.

### Ver diferencias

```bash
git diff
```

Muestra los cambios que todavía no fueron preparados.

Para revisar los cambios preparados:

```bash
git diff --cached
```

### Validar espacios y formato

```bash
git diff --check
```

Busca problemas como espacios en blanco al final de líneas.

### Enviar cambios a GitHub

```bash
git push origin main
```

Publica los commits locales en la rama `main`.

---

# 🔐 Comandos relacionados con secretos

### Comprobar que `.env` no está versionado

```bash
git ls-files .env
```

No debe devolver resultados.

### Comprobar que `.env` está siendo ignorado

```bash
git check-ignore -v .env
```

Debe indicar la regla correspondiente de `.gitignore`.

### Buscar posibles credenciales antes del commit

```bash
git diff --cached | grep -niE 'password|token|secret'
```

Esta verificación permitió detectar que el reporte HTML generado por ZAP podía contener las credenciales
utilizadas durante el análisis.

Por este motivo el reporte generado localmente no se versiona y se conserva como Artifact del pipeline.

---

# 🧩 Problemas encontrados y soluciones

Durante el desarrollo se presentaron diferentes inconvenientes que fueron utilizados como parte del proceso de
diagnóstico.

### Sesiones con dos workers de Gunicorn

Inicialmente Gunicorn utilizaba:

```text
--workers=2
```

La sesión se almacenaba en memoria mediante:

```python
SESSION_TOKEN
```

Al existir dos procesos independientes, un login podía ejecutarse en un worker y la siguiente petición llegar a
otro proceso sin conocer el token.

Se solucionó utilizando:

```text
--workers=1
```

para esta implementación didáctica basada en sesión en memoria.

---

### Acceso del contenedor ZAP a la aplicación

Inicialmente se utilizó:

```text
host.docker.internal
```

y se comprobó su acceso desde un contenedor.

Sin embargo, GitHub Actions ejecuta `action-af` utilizando:

```text
--network=host
```

y no resuelve automáticamente `host.docker.internal`.

Finalmente el plan de ZAP utiliza:

```text
http://localhost
```

que es accesible dentro del contenedor de ZAP debido al uso de la red del host.

---

### Parámetro `token` de GitHub Actions

La versión utilizada:

```text
zaproxy/action-af@v0.3.0
```

no admite `token` como input.

Por ese motivo se eliminó esa configuración del workflow y se utilizaron únicamente los parámetros soportados por
la acción.

---

### Generación del reporte

Durante las pruebas el reporte podía producir conflictos cuando ya existía una salida anterior.

Se utilizó un nombre específico para las ejecuciones del pipeline y se preparó el directorio `reports/` con
permisos adecuados antes de ejecutar ZAP.

---

# ✅ Resultado final

El resultado final del TP fue un pipeline de seguridad automatizado que integra:

```text
Notes App
    ↓
Docker Compose
    ↓
Autenticación
    ↓
GitHub Secrets
    ↓
GitHub Actions
    ↓
OWASP ZAP Automation Framework
    ↓
Spider
    ↓
Ajax Spider
    ↓
Passive Scan
    ↓
Active Scan autenticado
    ↓
Reporte
    ↓
GitHub Artifact
    ↓
✅ Workflow exitoso
```

La ejecución final de GitHub Actions terminó correctamente, demostrando que la aplicación puede ser levantada y
analizada automáticamente como parte del proceso de CI/CD.

---

# 📌 Conclusión

La implementación permitió integrar la seguridad al ciclo de desarrollo de la Notes App mediante un enfoque
DevSecOps. Se pasó de controles principalmente operativos y estáticos a incorporar un análisis dinámico de la
aplicación en ejecución.

La integración de OWASP ZAP mediante Automation Framework permitió automatizar el descubrimiento de recursos, el
análisis pasivo y las pruebas activas, incluyendo el acceso autenticado a los endpoints protegidos.

El uso de GitHub Secrets permitió mantener separadas las credenciales de la aplicación respecto del código fuente
y del pipeline. A su vez, GitHub Actions permitió ejecutar el proceso automáticamente ante cambios en el
repositorio y almacenar los resultados como artifacts.

Finalmente, la ejecución exitosa del workflow confirma que el análisis DAST quedó integrado dentro del proceso de
CI/CD, proporcionando una base reproducible para detectar problemas de seguridad antes de que los cambios lleguen
 a etapas posteriores del desarrollo.
