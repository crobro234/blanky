import { useState, useEffect } from "react";
import axios from "axios";
import "./App.css";

const API = "https://blanky.onrender.com";

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
  const [messageType, setMessageType] = useState("");

  const [score, setScore] = useState({ correct: 0, total: 0 });

  useEffect(() => {
    localStorage.setItem("theme", theme);
  }, [theme]);

  const currentQuestion = questions[currentIndex];

  const percent =
    score.total === 0 ? 0 : Math.round((score.correct / score.total) * 100);

  const progress =
    questions.length === 0
      ? 0
      : Math.round(((currentIndex + 1) / questions.length) * 100);

  const toggleTheme = () => {
    setTheme((prev) => (prev === "dark" ? "light" : "dark"));
  };

  const uploadFile = async () => {
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    const res = await axios.post(`${API}/upload-txt`, formData);

    setQuestions(res.data.questions);
    setDocumentId(res.data.document_id);
    setCurrentIndex(0);
    setAnswer("");
    setChoices([]);
    setScore({ correct: 0, total: 0 });
  };

  const loadReview = async () => {
    if (!documentId) return;

    const res = await axios.get(
      `${API}/review-questions/${documentId}`
    );

    setQuestions(res.data.review);
    setCurrentIndex(0);
  };

  const loadChoices = async (index) => {
    const res = await axios.get(
      `${API}/multiple-choice/${documentId}/${index}`
    );
    setChoices(res.data.choices);
  };

  const checkAnswer = async () => {
    const res = await axios.post(`${API}/check-answer`, null, {
      params: {
        document_id: documentId,
        index: currentIndex,
        user_answer: answer,
      },
    });

    if (res.data.correct) {
      if (res.data.next_same_question) {
        setQuestions((prev) => {
          const copy = [...prev];
          copy[currentIndex] = {
            ...copy[currentIndex],
            question: res.data.question,
            answer: res.data.answer,
          };
          return copy;
        });
        setAnswer("");
        return;
      }

      setScore((p) => ({
        correct: p.correct + 1,
        total: p.total + 1,
      }));

      setTimeout(next, 500);
    } else {
      setMessage("오답");
    }
  };

  const checkChoice = async (choice) => {
    const correct = choice === currentQuestion.answer;

    await axios.post(`${API}/record-result`, null, {
      params: {
        document_id: documentId,
        index: currentIndex,
        is_correct: correct,
      },
    });

    setScore((p) => ({
      correct: p.correct + (correct ? 1 : 0),
      total: p.total + 1,
    }));

    setTimeout(next, 500);
  };

  const next = async () => {
    const nextIndex = currentIndex + 1;

    if (nextIndex >= questions.length) return;

    setCurrentIndex(nextIndex);
    setAnswer("");

    if (mode === "multiple") {
      await loadChoices(nextIndex);
    }
  };

  return (
    <div className={`app ${theme}`}>
      <div className="shell">
        <div className="hero">
          <h1>Blanky</h1>

          <div>
            <button onClick={toggleTheme}>
              {theme === "dark" ? "화이트" : "다크"}
            </button>
            <span>{percent}점</span>
          </div>
        </div>

        <div className="panel">
          <input
            type="file"
            accept=".txt"
            onChange={(e) => setFile(e.target.files[0])}
          />
          <button onClick={uploadFile}>업로드</button>
          <button onClick={loadReview}>오답복습</button>
        </div>

        {currentQuestion && (
          <div className="panel">
            <p>{currentQuestion.question}</p>

            <div>
              <button onClick={() => setMode("subjective")}>
                주관식
              </button>
              <button
                onClick={async () => {
                  setMode("multiple");
                  await loadChoices(currentIndex);
                }}
              >
                객관식
              </button>
            </div>

            {mode === "subjective" && (
              <>
                <input
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                />
                <button onClick={checkAnswer}>확인</button>
              </>
            )}

            {mode === "multiple" &&
              choices.map((c, i) => (
                <button key={i} onClick={() => checkChoice(c)}>
                  {c}
                </button>
              ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
