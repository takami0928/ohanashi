import { useState } from "react";

import { api, type TurnResponse } from "../api/client";

type DevScreenProps = {
  storageDriver: string;
};

export function DevScreen({ storageDriver }: DevScreenProps) {
  const [textInput, setTextInput] = useState("");
  const [result, setResult] = useState<TurnResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit() {
    if (!textInput.trim()) {
      return;
    }
    setLoading(true);
    setError("");
    try {
      const next = await api.devTurn({
        sessionId: "dev-session",
        textInput,
        recordingSeconds: 10,
        debug: true,
      });
      setResult(next);
    } catch {
      setError("ローカルサーバーにつながりません。");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="dev-screen">
      <div className="panel">
        <p className="eyebrow">開発確認</p>
        <h2>テキスト入力フォールバック</h2>
        <textarea
          rows={5}
          value={textInput}
          onChange={(event) => setTextInput(event.target.value)}
          placeholder="例: きょうりゅうがすき / しりとりしよう / おやすみ"
        />
        <button className="talk-button" disabled={loading} onClick={submit}>
          {loading ? "かんがえ中" : "送って確認"}
        </button>
        <p className="helper-text">この画面の文字起こし表示は保存されません。保存先ドライバ: {storageDriver}</p>
        {error ? <p className="error-text">{error}</p> : null}
      </div>

      {result?.debug ? (
        <div className="panel-grid">
          <section className="panel">
            <h3>その場の入力</h3>
            <p>{String(result.debug.transcript ?? "")}</p>
          </section>
          <section className="panel">
            <h3>返答</h3>
            <p>{result.response_text}</p>
          </section>
          <section className="panel">
            <h3>判定</h3>
            <ul className="plain-list">
              <li>mode: {result.mode}</li>
              <li>safety: {result.safety_level}</li>
              <li>path: {String(result.debug.responsePath ?? "")}</li>
              <li>sessionAction: {String(result.debug.sessionAction ?? "")}</li>
              <li>used_llm: {String(result.used_llm)}</li>
            </ul>
          </section>
        </div>
      ) : null}
    </section>
  );
}

