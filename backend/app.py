import datetime
import os
import secrets
import psycopg2
from flask import Flask, jsonify, request

app = Flask(__name__)

APP_USER = os.getenv("APP_USER", "admin")
APP_PASSWORD = os.getenv("APP_PASSWORD", "")

# Token de sesión en memoria para el entorno de pruebas
SESSION_TOKEN = None


def get_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "db"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "notesdb"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "devops123")
    )


def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS notes (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(200) NOT NULL,
                    content TEXT NOT NULL DEFAULT '',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )


def require_auth():
    global SESSION_TOKEN

    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        return False

    token = auth_header[7:]

    return SESSION_TOKEN is not None and secrets.compare_digest(
        token, SESSION_TOKEN
    )


@app.get("/health")
def health():
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")

        return jsonify(
            status="ok",
            db="connected",
            time=datetime.datetime.now(datetime.timezone.utc).isoformat()
        )

    except Exception as exc:
        return jsonify(
            status="error",
            db="disconnected",
            detail=str(exc)
        ), 503


@app.post("/api/login")
def login():
    global SESSION_TOKEN

    data = request.get_json(silent=True) or {}

    username = str(data.get("username", ""))
    password = str(data.get("password", ""))

    if not secrets.compare_digest(username, APP_USER) or not secrets.compare_digest(
        password, APP_PASSWORD
    ):
        return jsonify(error="credenciales inválidas"), 401

    SESSION_TOKEN = secrets.token_urlsafe(32)

    return jsonify(
        message="autenticación correcta",
        token=SESSION_TOKEN
    )


@app.get("/api/notes")
def list_notes():
    if not require_auth():
        return jsonify(error="autenticación requerida"), 401

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id,title,content,created_at FROM notes ORDER BY id"
            )

            return jsonify([
                {
                    "id": r[0],
                    "title": r[1],
                    "content": r[2],
                    "created_at": r[3].isoformat()
                }
                for r in cur.fetchall()
            ])


@app.get("/api/notes/<int:note_id>")
def read_note(note_id):
    if not require_auth():
        return jsonify(error="autenticación requerida"), 401

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id,title,content,created_at
                FROM notes
                WHERE id=%s
                """,
                (note_id,)
            )

            row = cur.fetchone()

    if row:
        return jsonify(
            id=row[0],
            title=row[1],
            content=row[2],
            created_at=row[3].isoformat()
        ), 200

    return jsonify(error="nota no encontrada"), 404


@app.post("/api/notes")
def create_note():
    if not require_auth():
        return jsonify(error="autenticación requerida"), 401

    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()

    if not title or len(title) > 200:
        return jsonify(
            error="title es obligatorio y admite hasta 200 caracteres"
        ), 400

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO notes(title,content)
                VALUES(%s,%s)
                RETURNING id
                """,
                (title, str(data.get("content", "")))
            )

            note_id = cur.fetchone()[0]

    return jsonify(
        id=note_id,
        message="nota creada"
    ), 201


@app.delete("/api/notes/<int:note_id>")
def delete_note(note_id):
    if not require_auth():
        return jsonify(error="autenticación requerida"), 401

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM notes
                WHERE id=%s
                RETURNING id
                """,
                (note_id,)
            )

            deleted = cur.fetchone()

    if deleted:
        return jsonify(message="nota eliminada"), 200

    return jsonify(error="nota no encontrada"), 404


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
