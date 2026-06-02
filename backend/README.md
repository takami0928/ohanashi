# Backend

ローカル会話オーケストレーターのバックエンドです。

## 役割

- 音声または開発用テキスト入力を受け取る
- 安全判定を LLM より先に行う
- モード判定、セッション終了判定、記憶カード更新を行う
- ローカル LLM / ASR / TTS がなければフォールバックする
- 会話全文、音声、文字起こし全文ログを永続保存しない

## 起動

推奨:

```bash
uvicorn backend.app.main:app --reload
```

FastAPI / Uvicorn 未導入でも最低限動作確認したい場合:

```bash
py -3.8 -m backend.app.main
```

## 環境変数

- `LOCAL_LLM_PROVIDER=ollama`
- `OLLAMA_URL=http://127.0.0.1:11434/api/generate`
- `OLLAMA_MODEL=qwen2.5:3b`
- `LOCAL_ASR_PROVIDER=command`
- `ASR_COMMAND=<input> を受け取って文字起こしを stdout に出すコマンド`
- `LOCAL_TTS_PROVIDER=voicevox`
- `VOICEVOX_URL=http://127.0.0.1:50021`
- `VOICEVOX_SPEAKER=1`

## 保存方針

- 保存する: 設定、記憶カード、利用時間集計
- 保存しない: 会話全文、音声、子どもの発話原文、文字起こし全文ログ

## ストレージ

- 通常は SQLite を優先します
- `sqlite3` が利用できない環境では JSON フォールバックを使います

