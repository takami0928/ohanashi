# しゃべるぬいぐるみの脳・ローカル会話オーケストレーター版 MVP

5歳児向けの「しゃべるぬいぐるみ」の脳だけを、ローカル完結で動かす MVP です。

## この MVP の方針

- ローカル LLM 中心ではなく、会話オーケストレーター中心
- 安全応答、秘密、薬、危険行動、個人情報、終了処理はルールとテンプレートで処理
- LLM はごっこ冒険、お話づくり、長めのおしゃべり補助に限定
- 会話全文、音声、文字起こし全文ログは永続保存しない
- 親画面では利用時間、記憶カード、設定だけ管理できる

## ディレクトリ

- `backend/app`: オーケストレーター、判定、保存、ローカルAI抽象化
- `backend/tests`: 安全判定、モード判定、LLM利用判定、記憶可否、終了判定、非保存テスト
- `frontend/src`: 子ども画面、親画面、開発画面

## 実装済み機能

- FastAPI 互換のバックエンド入口と、依存未導入時のフォールバックHTTPサーバー
- 会話オーケストレーターの処理順序
- 安全レベル 0-3 判定
- 5モード判定と曖昧時の2択誘導
- 固定テンプレート応答
- LLM / ASR / TTS 抽象クライアント
- SQLite 優先ストレージと JSON フォールバック
- 子ども画面、親画面、開発画面
- 会話全文・音声・文字起こし全文ログを永続保存しない設計
- PWA 用 manifest / service worker

## 起動手順

### 1. バックエンド

推奨 Python:

- 第一候補: `sqlite3` がそのまま使える公式 Python 3.10 - 3.12
- この作業環境での検証実績: `py -3.8` (`C:\ProgramData\Anaconda3\python.exe`) + backend venv

SQLite 確認コマンド:

```powershell
py -3.8 -c "import sqlite3; print(sqlite3.sqlite_version)"
```

この作業環境では、Anaconda の DLL 探索の都合で上のコマンドがそのままだと失敗し、次のようなエラーが出ました。

```text
ImportError: DLL load failed while importing _sqlite3: 指定されたモジュールが見つかりません。
```

これは `sqlite3` 本体ではなく、Python 実行時に `_sqlite3.pyd` が依存する DLL を見つけられていない意味です。

backend venv 作成手順:

```powershell
py -3.8 -m venv backend\.venv
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
backend\.venv\Scripts\python.exe -m pip install pytest
```

Windows の Anaconda 系 Python では、`C:\ProgramData\Anaconda3\Library\bin` を `PATH` に含めて起動すると `_sqlite3` と `_ssl` が安定します。リポジトリにはそのための起動スクリプト [backend/run_backend.ps1](</C:/Users/kouhei takami/Documents/Codex/2026-06-02/mvp-5-mvp-web-pwa-ai/backend/run_backend.ps1>) を含めています。

backend 起動:

```powershell
powershell -ExecutionPolicy Bypass -File backend\run_backend.ps1
```

または手動で起動する場合:

```powershell
$env:PATH='C:\ProgramData\Anaconda3\Library\bin;' + $env:PATH
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 2. フロントエンド

```bash
cd frontend
npm install
npm run dev
```

スマホなど別端末から同一 Wi-Fi でアクセスする場合:

```bash
cd frontend
npm run dev -- --host 0.0.0.0
```

### 3. アクセス

- フロント: `http://127.0.0.1:5173`
- バックエンド: `http://127.0.0.1:8000`

health 確認:

```powershell
Invoke-WebRequest -UseBasicParsing http://localhost:8000/api/health | Select-Object -ExpandProperty Content
```

正常:

```json
{"ok":true,"storageDriver":"sqlite"}
```

`storageDriver: "json-fallback"` の場合は、Python 側の `sqlite3` が使えていない可能性があります。

### 4. スマホからのアクセス

PC の IPv4 アドレス確認:

```powershell
ipconfig
```

`IPv4 Address` に表示された値を使って、スマホから次の形式でアクセスします。

```text
http://<PCのIPv4アドレス>:5173
```

例:

```text
http://192.168.1.20:5173
```

前提:

- PC とスマホが同じ Wi-Fi に接続されている
- frontend を `npm run dev -- --host 0.0.0.0` で起動している
- backend は PC 上で起動済みである

Windows ファイアウォールで詰まる場合の確認項目:

- `node.exe` または `npm` の受信がブロックされていないか
- `5173` 番ポートへのローカルネットワーク接続が遮断されていないか
- 初回起動時の「プライベートネットワークで許可」を拒否していないか
- セキュリティソフトがローカル HTTP 通信を遮断していないか
- `http://127.0.0.1:5173` は PC で開けるがスマホからだけ開けない場合、まずファイアウォールと `--host 0.0.0.0` を疑う

## テスト

この環境では pytest の自動ロードプラグインがハングしたため、以下で実行します。

```bash
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
py -3.8 -m pytest backend/tests -q
```

## SQLite の現状

今回の復旧作業では、backend venv + [backend/run_backend.ps1](</C:/Users/kouhei takami/Documents/Codex/2026-06-02/mvp-5-mvp-web-pwa-ai/backend/run_backend.ps1>) で `/api/health` が `storageDriver: "sqlite"` を返すことを確認しました。

注意点:

- `py -3.8 -c "import sqlite3; print(sqlite3.sqlite_version)"` 単体では、Anaconda の DLL 探索不足で失敗することがあります
- backend 側では [backend/app/db.py](</C:/Users/kouhei takami/Documents/Codex/2026-06-02/mvp-5-mvp-web-pwa-ai/backend/app/db.py>) で Windows の DLL 探索パスを補い、SQLite を優先します
- それでも `json-fallback` になる場合は、SQLite 付きの公式 Python を入れるか、`sqlite3` が使える Python で venv を作り直してください
- fallback でも、会話全文・音声・文字起こし全文ログは保存しません

## ローカル実機確認チェックリスト

- [ ] backend を `powershell -ExecutionPolicy Bypass -File backend\run_backend.ps1` で起動できる
- [ ] `http://localhost:8000/api/health` が `{"ok":true,"storageDriver":"sqlite"}` を返す
- [ ] frontend を `npm run dev -- --host 0.0.0.0` で起動できる
- [ ] PC ブラウザで子ども画面を開ける
- [ ] PC ブラウザで親画面を開ける
- [ ] PC ブラウザで開発画面を開ける
- [ ] 開発画面のテキスト入力で返答が得られる
- [ ] 子ども画面がチャットログ表示になっていない
- [ ] 親画面に会話全文が表示されない
- [ ] スマホから `http://<PCのIPv4アドレス>:<frontend port>` でアクセスできる
- [ ] 会話全文・音声・文字起こし全文ログが永続保存されない

## モックとフォールバック

- ASR 未導入: 開発画面のテキスト入力で代替
- LLM 未導入: テンプレート / ルール応答で代替
- TTS 未導入: ブラウザ `speechSynthesis` で代替

## 保存するもの / しないもの

保存するもの:

- ぬいぐるみ名
- 子どもの呼び名
- 好きなもの
- 好きな遊び
- ごっこ遊びの続き
- 抽象化した最近の軽い話題
- 利用時間集計

保存しないもの:

- 会話全文
- 音声データ
- 文字起こし全文ログ
- 親への不満の内容
- 秘密として話された内容
- 痛い話、怖い話、薬や病気の詳細
- 住所、園名、友達のフルネーム

## 今後の課題

- 実機の `whisper.cpp` / `faster-whisper` 接続を固定化する
- Ollama プロンプトを mode ごとにもう少し細かく最適化する
- VOICEVOX 接続時の話速・感情パラメータ調整を増やす
- 本番用には SQLite が使える Python 環境をそろえる
- 子ども画面の録音 UX と音声権限エラー導線をさらに詰める
