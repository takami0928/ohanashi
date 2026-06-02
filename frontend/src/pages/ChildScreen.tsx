import { useEffect, useRef, useState } from "react";

import type { Settings, TurnResponse } from "../api/client";
import { api } from "../api/client";
import { FaceCard } from "../components/FaceCard";

type ChildScreenProps = {
  settings: Settings;
};

export function ChildScreen({ settings }: ChildScreenProps) {
  const [status, setStatus] = useState("きいてるよ");
  const [reply, setReply] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [error, setError] = useState("");
  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const startedAtRef = useRef<number>(0);
  const sessionIdRef = useRef(`child-${Date.now()}`);

  useEffect(() => {
    return () => {
      streamRef.current?.getTracks().forEach((track) => track.stop());
      if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  async function toggleRecording() {
    setError("");

    if (isRecording && recorderRef.current) {
      recorderRef.current.stop();
      setIsRecording(false);
      setStatus("かんがえ中");
      return;
    }

    if (!navigator.mediaDevices || typeof MediaRecorder === "undefined") {
      setError("この端末では声入力が使えません。開発画面のテキスト入力で確認してください。");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      chunksRef.current = [];
      startedAtRef.current = Date.now();

      const recorder = new MediaRecorder(stream);
      recorderRef.current = recorder;
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };
      recorder.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
        const audioBase64 = await blobToBase64(blob);
        const recordingSeconds = Math.max(1, Math.round((Date.now() - startedAtRef.current) / 1000));
        await sendTurn(audioBase64, recordingSeconds);
        stream.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      };
      recorder.start();
      setIsRecording(true);
      setStatus("きいてるよ");
    } catch {
      setError("マイクが使えませんでした。開発画面でテキスト入力を使ってください。");
    }
  }

  async function sendTurn(audioBase64: string, recordingSeconds: number) {
    try {
      const result = await api.childTurn({
        sessionId: sessionIdRef.current,
        audioBase64,
        recordingSeconds,
      });
      handleTurnResult(result);
    } catch {
      setStatus("ちょっと休憩");
      setError("ローカルサーバーにつながりません。");
    }
  }

  function handleTurnResult(result: TurnResponse) {
    setStatus(result.state_label);
    setReply(result.response_text);
    if (result.audio_base64) {
      const audio = new Audio(`data:audio/wav;base64,${result.audio_base64}`);
      audio.play().catch(() => speakFallback(result.response_text));
    } else {
      speakFallback(result.response_text);
    }
  }

  function speakFallback(text: string) {
    if (!settings.voice_enabled || !("speechSynthesis" in window)) {
      return;
    }
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "ja-JP";
    utterance.rate = settings.speech_rate;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
  }

  return (
    <section className="child-screen">
      <FaceCard name={settings.toy_name || "もこ"} stateLabel={status} currentReply={reply} />
      <button className={`talk-button ${isRecording ? "talk-button--active" : ""}`} onClick={toggleRecording}>
        {isRecording ? "きくのをおわる" : "おはなしする"}
      </button>
      <button className="secondary-button" onClick={() => setReply("")}>
        もう一回
      </button>
      <p className="helper-text">おはなしの文字ログはのこしません。</p>
      {error ? <p className="error-text">{error}</p> : null}
    </section>
  );
}

async function blobToBase64(blob: Blob): Promise<string> {
  const arrayBuffer = await blob.arrayBuffer();
  let binary = "";
  const bytes = new Uint8Array(arrayBuffer);
  bytes.forEach((value) => {
    binary += String.fromCharCode(value);
  });
  return btoa(binary);
}

