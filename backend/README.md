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

```powershell
powershell -ExecutionPolicy Bypass -File .\run_backend.ps1
```

手動起動:

```powershell
$env:PATH='C:\ProgramData\Anaconda3\Library\bin;' + $env:PATH
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
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
- `storageDriver: sqlite` が正常です
- `storageDriver: json-fallback` の場合は Python 側の `sqlite3` が使えていない可能性があります
- `py -3.8` で `_sqlite3` DLL load failed が出る場合は、`_sqlite3.pyd` の依存 DLL 探索が不足している意味です
- この作業環境では `C:\ProgramData\Anaconda3\Library\bin` を `PATH` に含め、backend venv から起動することで SQLite を利用できました

## セットアップ確認

SQLite 確認:

```powershell
backend\.venv\Scripts\python.exe -c "from app.db import create_storage; from pathlib import Path; print(create_storage(Path('data')).driver)"
```

期待値:

```text
sqlite
```

health 確認:

```powershell
Invoke-WebRequest -UseBasicParsing http://localhost:8000/api/health | Select-Object -ExpandProperty Content
```

期待値:

```json
{"ok":true,"storageDriver":"sqlite"}
```
