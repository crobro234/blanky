import { useState, useEffect } from "react";
import axios from "axios";
import "./App.css";

const API = "http://127.0.0.1:8001";

function App() {
  const [file, setFile] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [documentId, setDocumentId] = useState(null);

  const [mode, setMode] = useState("subjective");
  const [theme, setTheme] = useState(
  localStorage.getItem("theme") || "dark"
);
  const [answer, setAnswer] = useState("");
  const [choices, setChoices] = useState([]);

  const [message, setMessage] = useState("");
  const [score, setScore] = useState({ correct: 0, total: 0 });

  const currentQuestion = questions[currentIndex];
  const toggleTheme = () => {
  setTheme((prev) => (prev === "dark" ? "light" : "dark"));
  };
  const percent =
    score.total === 0 ? 0 : Math.round((score.correct / score.total) * 100);
    useEffect(() => {
    localStorage.setItem("theme", theme);
    }, [theme]);
  const uploadFile = async () => {
    if (!file) {
      alert("TXT 파일을 선택하세요.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    const res = await axios.post(`${API}/upload-txt`, formData);

    setQuestions(res.data.questions);
    setDocumentId(res.data.document_id);
    setCurrentIndex(0);
    setAnswer("");
    setMessage("");
    setChoices([]);
    setScore({ correct: 0, total: 0 });

    if (mode === "multiple") {
      await loadMultipleChoice(0);
    }
  };

  const loadReviewQuestions = async () => {
    if (!documentId) {
      setMessage("먼저 TXT 파일 업로드");
      return;
    }

    const res = await axios.get(
      `${API}/review-questions/${documentId}`
    );

    if (res.data.review.length === 0) {
      setMessage("복습할 오답이 없습니다.");
      return;
    }

    setQuestions(res.data.review);
    setCurrentIndex(0);
    setAnswer("");
    setChoices([]);
    setMessage("");
    setScore({ correct: 0, total: 0 });

    if (mode === "multiple") {
      await loadMultipleChoice(0);
    }
  };

  const loadMultipleChoice = async (index) => {
    if (!documentId) return;

    const res = await axios.get(
      `${API}/multiple-choice/${documentId}/${index}`
    );

    setChoices(res.data.choices);
  };

  const changeMode = async (newMode) => {
    setMode(newMode);
    setMessage("");
    setAnswer("");

    if (newMode === "multiple" && questions.length > 0) {
      await loadMultipleChoice(currentIndex);
    }
  };

  const checkSubjectiveAnswer = async () => {
    if (!answer.trim() || !documentId) return;

    const res = await axios.post(`${API}/check-answer`, null, {
      params: {
        document_id: documentId,
        index: currentIndex,
        user_answer: answer,
      },
    });

    const isCorrect = res.data.correct;
    const wrongCount = res.data.wrong_count;

    if (isCorrect) {
      if (res.data.next_same_question) {
        setMessage("정답 / 같은 문장 다음 빈칸");

        setQuestions((prev) => {
          const updated = [...prev];
          updated[currentIndex] = {
            ...updated[currentIndex],
            question: res.data.question,
            answer: res.data.answer,
          };
          return updated;
        });

        setAnswer("");
        return;
      }

      setMessage("정답");
      setScore((prev) => ({
        correct: prev.correct + 1,
        total: prev.total + 1,
      }));

      setTimeout(goNext, 500);
    } else {
      if (wrongCount >= 3) {
        setMessage(`3회 실패 / 정답: ${res.data.real_answer}`);
        setScore((prev) => ({
          correct: prev.correct,
          total: prev.total + 1,
        }));

        setTimeout(goNext, 900);
      } else {
        setMessage(`오답 (${wrongCount}/3)`);
      }
    }
  };

  const checkMultipleChoiceAnswer = async (choice) => {
    if (!documentId) return;

    const realAnswer = questions[currentIndex].answer;
    const isCorrect = choice === realAnswer;

    await axios.post(`${API}/record-result`, null, {
      params: {
        document_id: documentId,
        index: currentIndex,
        is_correct: isCorrect,
      },
    });

    if (isCorrect) {
      setMessage("정답");
      setScore((prev) => ({
        correct: prev.correct + 1,
        total: prev.total + 1,
      }));

      setTimeout(goNext, 500);
    } else {
      setMessage(`오답 / 정답: ${realAnswer}`);
      setScore((prev) => ({
        correct: prev.correct,
        total: prev.total + 1,
      }));

      setTimeout(goNext, 900);
    }
  };

  const goNext = async () => {
    if (currentIndex + 1 < questions.length) {
      const nextIndex = currentIndex + 1;

      setCurrentIndex(nextIndex);
      setAnswer("");
      setMessage("");

      if (mode === "multiple") {
        await loadMultipleChoice(nextIndex);
      }
    } else {
      setMessage("모든 문제 완료");
    }
  };

  return (
    <div className={`app ${theme}`}>
      <div className="card">
        <h1>Blanky</h1>
        <button onClick={toggleTheme}>
        {theme === "dark" ? "화이트" : "다크"}
        </button>
        <div className="upload-box">
          <input
            type="file"
            accept=".txt"
            onChange={(e) => setFile(e.target.files[0])}
          />
          <button onClick={uploadFile}>TXT 업로드</button>
          <button onClick={loadReviewQuestions}>오답 복습</button>
        </div>

        {questions.length > 0 && (
          <div className="quiz-box">
            <div className="top-row">
              <span>
                문제 {currentIndex + 1} / {questions.length}
              </span>
              <span>점수 {percent}점</span>
            </div>

            <div className="mode-row">
              <button onClick={() => changeMode("subjective")}>
                주관식
              </button>
              <button onClick={() => changeMode("multiple")}>
                객관식
              </button>
            </div>

            <div className="question">{currentQuestion.question}</div>

            {mode === "subjective" && (
              <>
                <input
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") checkSubjectiveAnswer();
                  }}
                />
                <button onClick={checkSubjectiveAnswer}>
                  정답 확인
                </button>
              </>
            )}

            {mode === "multiple" &&
              choices.map((choice, i) => (
                <button
                  key={i}
                  onClick={() => checkMultipleChoiceAnswer(choice)}
                >
                  {choice}
                </button>
              ))}

            {message && <p>{message}</p>}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;