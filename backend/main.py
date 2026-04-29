from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from file_parser import parse_txt_file
from quiz import (
    make_blank_questions,
    check_answer,
    update_result,
    generate_choices,
    get_next_blank_from_line
)

from database import (
    init_db,
    create_document,
    save_questions,
    get_questions,
    get_question_by_index,
    update_question,
    get_review_questions
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⭐ 여기 수정
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def root():
    return {"message": "Blanky backend is running"}


@app.post("/upload-txt")
async def upload_txt(file: UploadFile = File(...)):
    text = await parse_txt_file(file)

    questions = make_blank_questions(text)
    document_id = create_document(file.filename)
    save_questions(document_id, questions)

    saved_questions = get_questions(document_id)

    return {
        "message": "TXT uploaded successfully",
        "document_id": document_id,
        "total_questions": len(saved_questions),
        "questions": saved_questions
    }


@app.get("/questions/{document_id}")
def get_all_questions(document_id: int):
    questions = get_questions(document_id)

    return {
        "document_id": document_id,
        "questions": questions,
        "total_questions": len(questions)
    }


@app.get("/question/{document_id}/{index}")
def get_question(document_id: int, index: int):
    q = get_question_by_index(document_id, index)

    if q is None:
        return {"error": "Question not found"}

    return {
        "index": index,
        "question": q["question"],
        "answer_length": len(q["answer"])
    }


@app.post("/check-answer")
def check_user_answer(document_id: int, index: int, user_answer: str):
    q = get_question_by_index(document_id, index)

    if q is None:
        return {"error": "Question not found"}

    current_answer = q["answer"]
    is_correct = check_answer(user_answer, current_answer)

    update_result(q, is_correct)

    if is_correct:
        next_word = get_next_blank_from_line(q["original"], q["used_answers"])

        if next_word:
            q["used_answers"].append(next_word)

            blank = "_" * max(len(next_word), 3)
            q["question"] = q["original"].replace(next_word, blank, 1)
            q["answer"] = next_word

            update_question(q)

            return {
                "correct": True,
                "next_same_question": True,
                "question": q["question"],
                "answer": q["answer"],
                "wrong_count": q["wrong_count"],
                "correct_count": q["correct_count"]
            }

    update_question(q)

    return {
        "correct": is_correct,
        "next_same_question": False,
        "user_answer": user_answer,
        "real_answer": current_answer,
        "wrong_count": q["wrong_count"],
        "correct_count": q["correct_count"]
    }


@app.post("/record-result")
def record_result(document_id: int, index: int, is_correct: bool):
    q = get_question_by_index(document_id, index)

    if q is None:
        return {"error": "Question not found"}

    update_result(q, is_correct)
    update_question(q)

    return {
        "correct": is_correct,
        "wrong_count": q["wrong_count"],
        "correct_count": q["correct_count"]
    }


@app.get("/review-questions/{document_id}")
def review_questions(document_id: int):
    review = get_review_questions(document_id)

    return {
        "document_id": document_id,
        "review": review
    }


@app.get("/multiple-choice/{document_id}/{index}")
def get_mc_question(document_id: int, index: int):
    q = get_question_by_index(document_id, index)

    if q is None:
        return {"error": "not found"}

    questions = get_questions(document_id)
    all_answers = [qq["answer"] for qq in questions]

    choices = generate_choices(q["answer"], all_answers)

    return {
        "question": q["question"],
        "choices": choices,
        "answer": q["answer"]
    }
