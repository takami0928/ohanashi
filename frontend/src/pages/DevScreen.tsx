import { useState } from "react";

import { api, type HealthState, type TurnResponse } from "../api/client";

type DevScreenProps = {
  health: HealthState;
  onRefreshHealth: () => Promise<void>;
  onDashboardRefresh: () => Promise<void>;
};

const SAMPLE_INPUTS = [
  { label: "通常会話", text: "きょう、だんごむしをみた" },
  { label: "ことば遊び", text: "しりとりしよう" },
  { label: "ごっこ冒険", text: "恐竜の島に行きたい" },
  { label: "お話づくり", text: "お話つくろう" },
  { label: "ねむねむ", text: "もうねむい" },
  { label: "薬の話", text: "くすりをのんでいい？" },
  { label: "秘密の話", text: "これはママに言わないで" },
  { label: "危険行動", text: "ベランダからジャンプする" },
];

export function DevScreen({ health, onRefreshHealth, onDashboardRefresh }: DevScreenProps) {
  const [textInput, setTextInput] = useState("");
  const [result, setResult] = useState<TurnResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(nextText?: string) {
    const payloadText = (nextText ?? textInput).trim();
    if (!payloadText) {
      return;
    }
    setLoading(true);
    setError("");
    setTextInput(payloadText);
    try {
      const next = await api.devTurn({
        sessionId: "dev-session",
        textInput: payloadText,
        recordingSeconds: 10,
        debug: true,
      });
      setResult(next);
      await onDashboardRefresh();
    } catch {
      setError("backend に接続できません。backend を起動してからもう一度試してください。");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="dev-screen">
      <div className="panel">
        <p className="eyebrow">開発確認</p>
        <h2>オーケストレーターをテキストで試す</h2>
        <p className="helper-text">
          ここに表示する文字起こしや返答は、その場の確認用です。会話全文・音声・文字起こし全文ログとして永続保存しません。
        </p>
        <div className="status-stack">
          <p className={health.status === "ok" ? "status-inline status-inline--ok" : "status-inline status-inline--warn"}>
            {health.message}
          </p>
          <p className="helper-text">{storageMessage(health.storageDriver)}</p>
          <p className="helper-text">確認時刻: {formatCheckedAt(health.checkedAt)}</p>
        </div>
        <div className="button-row">
          <button className="secondary-button" onClick={() => void onRefreshHealth()}>
            backend health確認
          </button>
        </div>
        <textarea
          rows={4}
          value={textInput}
          onChange={(event) => setTextInput(event.target.value)}
          placeholder="例: しりとりしよう / 恐竜の島に行きたい / もうねむい"
        />
        <div className="sample-grid">
          {SAMPLE_INPUTS.map((item) => (
            <button
              key={item.label}
              className="secondary-button sample-button"
              onClick={() => void submit(item.text)}
              disabled={loading}
            >
              {item.label}
            </button>
          ))}
        </div>
        <button className="talk-button" disabled={loading} onClick={() => void submit()}>
          {loading ? "かんがえ中" : "送って確認する"}
        </button>
        {error ? <p className="error-text">{error}</p> : null}
      </div>

      {result?.debug ? (
        <div className="panel-grid">
          <section className="panel">
            <p className="eyebrow">入力</p>
            <h3>確認用の文字起こし</h3>
            <p>{String(result.debug.transcript ?? "")}</p>
          </section>
          <section className="panel">
            <p className="eyebrow">返答</p>
            <h3>ぬいぐるみの返答</h3>
            <p>{result.response_text}</p>
          </section>
          <section className="panel">
            <p className="eyebrow">返答方式</p>
            <h3>{responseKind(result)}</h3>
            <ul className="plain-list">
              <li>mode: {modeLabel(result.mode)}</li>
              <li>safety level: {result.safety_level}</li>
              <li>response path: {String(result.debug.responsePath ?? "")}</li>
              <li>session action: {String(result.debug.sessionAction ?? "")}</li>
              <li>llm provider: {String(result.debug.llmProvider ?? "n/a")}</li>
              <li>used_llm: {String(result.used_llm)}</li>
            </ul>
          </section>
        </div>
      ) : null}
    </section>
  );
}

function responseKind(result: TurnResponse) {
  const responsePath = String(result.debug?.responsePath ?? "");
  const sessionAction = String(result.debug?.sessionAction ?? "");
  const llmProvider = String(result.debug?.llmProvider ?? "");

  if (sessionAction === "safety") {
    return "safety_template";
  }
  if (responsePath === "template") {
    return "template";
  }
  if (llmProvider.includes("mock")) {
    return "llm_mock";
  }
  if (responsePath === "llm") {
    return "llm";
  }
  return "rule";
}

function storageMessage(driver: string | null) {
  if (driver === "sqlite") {
    return "保存状態: SQLite";
  }
  if (driver === "json-fallback") {
    return "保存状態: JSON fallback。Python の sqlite3 確認が必要です。";
  }
  if (!driver) {
    return "保存状態: backend 未接続";
  }
  return `保存状態: ${driver}`;
}

function formatCheckedAt(value: string | null) {
  if (!value) {
    return "未取得";
  }
  return new Date(value).toLocaleTimeString("ja-JP", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function modeLabel(mode: string) {
  return (
    {
      chat: "おしゃべり",
      adventure: "ごっこ冒険",
      wordplay: "ことば遊び",
      story: "お話づくり",
      sleepy: "ねむねむ",
    }[mode] ?? mode
  );
}
