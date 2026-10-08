"""
Mural da Turma - exemplo de site com Python (Flask + SQLite).

Como rodar:
    pip install -r requirements.txt
    python app.py
Depois abra http://127.0.0.1:5000 no navegador.
"""
import os
import sqlite3
from pathlib import Path

from flask import Flask, flash, g, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "mural.db"

app = Flask(__name__)
# A chave protege as mensagens "flash". Em produção, defina a variável de ambiente.
app.secret_key = os.environ.get("SECRET_KEY", "troque-esta-chave-em-producao")
# Senha usada para apagar recados. Em produção, defina a variável de ambiente.
SENHA_PROFESSOR = os.environ.get("SENHA_PROFESSOR", "prof123")

TURMAS = ["1ºA", "1ºB", "1ºC", "2ºA", "2ºB", "2ºC", "3ºA", "3ºB", "3ºC"]


# ---------- Banco de dados (SQLite) ----------
def get_db():
    """Abre uma conexão por requisição e reaproveita dentro dela."""
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row  # permite acessar colunas pelo nome
    return g.db


@app.teardown_appcontext
def fechar_db(erro=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def criar_tabela():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS recados (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            nome      TEXT NOT NULL,
            turma     TEXT NOT NULL,
            mensagem  TEXT NOT NULL,
            criado_em TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
        """
    )
    conn.commit()
    conn.close()


# ---------- Rotas ----------
@app.route("/")
def index():
    """Lista os recados. Aceita filtro opcional: /?turma=3ºC"""
    turma = request.args.get("turma", "").strip()
    db = get_db()
    if turma in TURMAS:
        recados = db.execute(
            "SELECT * FROM recados WHERE turma = ? ORDER BY id DESC", (turma,)
        ).fetchall()
    else:
        turma = ""
        recados = db.execute("SELECT * FROM recados ORDER BY id DESC").fetchall()
    return render_template("index.html", recados=recados, turmas=TURMAS, filtro=turma)


@app.route("/recados", methods=["POST"])
def criar_recado():
    """Recebe o formulário, valida e grava no banco."""
    nome = request.form.get("nome", "").strip()
    turma = request.form.get("turma", "").strip()
    mensagem = request.form.get("mensagem", "").strip()

    if not nome or not mensagem or turma not in TURMAS:
        flash("Preencha nome, turma e mensagem para publicar.", "erro")
    elif len(nome) > 60 or len(mensagem) > 280:
        flash("O nome aceita até 60 caracteres e a mensagem até 280.", "erro")
    else:
        db = get_db()
        # Os "?" evitam SQL Injection: nunca monte SQL concatenando texto do usuário.
        db.execute(
            "INSERT INTO recados (nome, turma, mensagem) VALUES (?, ?, ?)",
            (nome, turma, mensagem),
        )
        db.commit()
        flash("Recado publicado no mural.", "ok")
    return redirect(url_for("index"))


@app.route("/recados/<int:recado_id>/apagar", methods=["POST"])
def apagar_recado(recado_id):
    """Apaga um recado se a senha do professor estiver correta."""
    if request.form.get("senha", "") != SENHA_PROFESSOR:
        flash("Senha incorreta. O recado não foi apagado.", "erro")
    else:
        db = get_db()
        db.execute("DELETE FROM recados WHERE id = ?", (recado_id,))
        db.commit()
        flash("Recado apagado.", "ok")
    return redirect(url_for("index"))


criar_tabela()

if __name__ == "__main__":
    app.run(debug=True)
