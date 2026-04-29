import sqlite3
import json
from pathlib import Path

DB_PATH = Path("blanky.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        original TEXT NOT NULL,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        used_answers TEXT NOT NULL,
        wrong_count INTEGER DEFAULT 0,
        correct_count INTEGER DEFAULT 0,
        FOREIGN KEY(document_id) REFERENCES documents(id)
    )
    """)

    conn.commit()
    conn.close()


def create_document(filename):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO documents (filename) VALUES (?)",
        (filename,)
    )

    document_id = cur.lastrowid
    conn.commit()
    conn.close()

    return document_id


def save_questions(document_id, questions):
    conn = get_conn()
    cur = conn.cursor()

    for q in questions:
        cur.execute("""
        INSERT INTO questions
        (document_id, original, question, answer, used_answers, wrong_count, correct_count)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            document_id,
            q["original"],
            q["question"],
            q["answer"],
            json.dumps(q["used_answers"], ensure_ascii=False),
            q["wrong_count"],
            q["correct_count"]
        ))

    conn.commit()
    conn.close()


def row_to_question(row):
    return {
        "id": row["id"],
        "document_id": row["document_id"],
        "original": row["original"],
        "question": row["question"],
        "answer": row["answer"],
        "used_answers": json.loads(row["used_answers"]),
        "wrong_count": row["wrong_count"],
        "correct_count": row["correct_count"]
    }


def get_questions(document_id):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM questions WHERE document_id = ?",
        (document_id,)
    )

    rows = cur.fetchall()
    conn.close()

    return [row_to_question(row) for row in rows]


def get_question_by_index(document_id, index):
    questions = get_questions(document_id)

    if index < 0 or index >= len(questions):
        return None

    return questions[index]


def update_question(question):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    UPDATE questions
    SET question = ?, answer = ?, used_answers = ?, wrong_count = ?, correct_count = ?
    WHERE id = ?
    """, (
        question["question"],
        question["answer"],
        json.dumps(question["used_answers"], ensure_ascii=False),
        question["wrong_count"],
        question["correct_count"],
        question["id"]
    ))

    conn.commit()
    conn.close()


def get_review_questions(document_id):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    SELECT * FROM questions
    WHERE document_id = ? AND wrong_count > 0
    """, (document_id,))

    rows = cur.fetchall()
    conn.close()

    return [row_to_question(row) for row in rows]