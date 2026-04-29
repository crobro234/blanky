import random
import re


STOPWORDS = {
    "the", "of", "is", "are", "a", "an", "to", "in", "on",
    "and", "or", "for", "with", "must", "be", "as", "by",
    "this", "that", "these", "those", "it", "its", "can",
    "will", "would", "should", "could", "from", "at", "if",
    "then", "than", "there", "their", "also"
}


def split_lines(text):
    lines = text.splitlines()
    clean_lines = []

    for line in lines:
        line = line.strip()
        if len(line) >= 5:
            clean_lines.append(line)

    return clean_lines


def get_words(line):
    return re.findall(r"[가-힣A-Za-z0-9]+", line)


def is_good_blank_word(word):
    if len(word) < 2:
        return False

    if word.lower() in STOPWORDS:
        return False

    # 숫자만 있는 단어는 제외
    if word.isdigit():
        return False

    # 영어는 너무 짧은 단어 제외
    if re.fullmatch(r"[A-Za-z]+", word) and len(word) < 4:
        return False

    return True


def score_word(word):
    score = 0

    # 긴 단어일수록 중요할 가능성 높음
    score += len(word)

    # 영어 대문자 포함: 용어/고유명사 가능성
    if re.search(r"[A-Z]", word):
        score += 3

    # 한글 3글자 이상: 용어 가능성
    if re.search(r"[가-힣]", word) and len(word) >= 3:
        score += 3

    # 숫자+문자 조합: 개념명 가능성, 예: L2, GPT4
    if re.search(r"[A-Za-z가-힣]", word) and re.search(r"[0-9]", word):
        score += 2

    return score


def pick_blank_word(line):
    words = get_words(line)

    candidates = []

    for word in words:
        if is_good_blank_word(word):
            candidates.append(word)

    if len(candidates) == 0:
        return None

    candidates.sort(key=score_word, reverse=True)

    # 항상 1등만 고르면 반복이 심해서 상위권 중 랜덤
    top_count = min(3, len(candidates))
    return random.choice(candidates[:top_count])


def make_blank_questions(text, frequency=1):
    lines = split_lines(text)
    questions = []

    for line in lines:
        answer = pick_blank_word(line)

        if answer is None:
            continue

        blank = "_" * max(len(answer), 3)
        question_text = line.replace(answer, blank, 1)

        questions.append({
    "original": line,
    "question": question_text,
    "answer": answer,
    "used_answers": [answer],   # 추가
    "wrong_count": 0,
    "correct_count": 0
})

    random.shuffle(questions)

    # frequency가 낮으면 일부만 출제
    if frequency < 1:
        frequency = 1

    return questions


def normalize_answer(answer):
    return answer.strip().lower()


def check_answer(user_answer, real_answer):
    return normalize_answer(user_answer) == normalize_answer(real_answer)


def update_result(question, is_correct):
    if is_correct:
        question["correct_count"] += 1
    else:
        question["wrong_count"] += 1
def get_question_weight(q):
    # 틀린 횟수는 가중치 ↑
    # 맞힌 횟수는 가중치 ↓
    return max(1, q["wrong_count"] * 3 - q["correct_count"])
def weighted_shuffle(questions):
    weighted = []

    for q in questions:
        w = get_question_weight(q)
        weighted.extend([q] * w)

    random.shuffle(weighted)
    return weighted
def is_korean(text):
    return bool(re.search(r"[가-힣]", text))


def is_english(text):
    return bool(re.search(r"[A-Za-z]", text))


def same_language(a, b):
    if is_korean(a) and is_korean(b):
        return True
    if is_english(a) and is_english(b):
        return True
    return False


def generate_choices(answer, all_answers):
    answer_clean = answer.strip()
    answer_key = answer_clean.lower()

    candidates = []

    for word in all_answers:
        word = word.strip()
        word_key = word.lower()

        if word_key == answer_key:
            continue

        if not is_good_blank_word(word):
            continue

        if not same_language(answer_clean, word):
            continue

        length_gap = abs(len(word) - len(answer_clean))
        candidates.append((length_gap, word))

    candidates.sort(key=lambda x: x[0])

    wrong = []
    used_lower = {answer_key}

    for _, word in candidates:
        word_key = word.lower()

        if word_key not in used_lower:
            wrong.append(word)
            used_lower.add(word_key)

        if len(wrong) == 4:
            break

    fallback_english = [
        "continuity", "function", "variable", "equation",
        "condition", "definition", "theorem", "value"
    ]

    fallback_korean = [
        "정의", "조건", "함수", "방정식",
        "정리", "값", "변수", "성질"
    ]

    fallback = fallback_korean if is_korean(answer_clean) else fallback_english

    for word in fallback:
        word_key = word.lower()

        if len(wrong) == 4:
            break

        if word_key not in used_lower:
            wrong.append(word)
            used_lower.add(word_key)

    choices = wrong[:4] + [answer_clean]
    random.shuffle(choices)

    return choices
def get_next_blank_from_line(line, used_answers):
    words = get_words(line)

    candidates = []

    for word in words:
        if is_good_blank_word(word) and word not in used_answers:
            candidates.append(word)

    if len(candidates) == 0:
        return None

    candidates.sort(key=score_word, reverse=True)

    return candidates[0]