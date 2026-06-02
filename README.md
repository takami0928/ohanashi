# しゃべるぬいぐるみの脳・ローカル会話オーケストレーター版 MVP

5歳児向けの「しゃべるぬいぐるみ」の脳だけを、家庭内のローカル環境で動かす MVP です。スマホ Web/PWA をぬいぐるみの近くに置き、子どもがぬいぐるみに話しかけている感覚を優先しています。

## 方針

- 外部 AI API は使いません
- 会話全文は保存しません
- 音声データは保存しません
- 文字起こし全文ログは保存しません
- 親画面に会話全文は表示しません
- 子ども画面はチャットログにしません
- SQLite が使える環境では SQLite を第一ストレージとして使います
- SQLite が使えない場合だけ JSON fallback を使います

## 画面の役割

- 子ども画面: 大きな「おはなしする」ボタンで話しかける画面です。最新の返答だけを表示します。
- 親画面: 利用時間、モード、記憶カード、設定、storageDriver を確認する画面です。監視画面ではありません。
- 開発画面: テキスト入力で orchestrator を試し、安全判定やモード判定を確認する画面です。表示内容は永続保存しません。

## backend 初回セットアップ

`backend/.venv` は Git 管理しないため、clone 直後は存在しません。

推奨:

- 公式 Python 3.10 から 3.12
- Anaconda Python 3.8 は `ssl` / `sqlite3` DLL 問題が出ることがあるため非推奨

Python 確認:

```powershell
py -0p
py -3.12 -c "import ssl, sqlite3; print(ssl.OPENSSL_VERSION); print(sqlite3.sqlite_version)"
```

セットアップ:

```powershell
cd D:\ohanashi\backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

補助スクリプトを使う場合:

```powershell
cd D:\ohanashi
powershell -ExecutionPolicy Bypass -File backend\setup_backend.ps1
```

backend 起動:

```powershell
cd D:\ohanashi
powershell -ExecutionPolicy Bypass -File backend\run_backend.ps1
```

health 確認:

```powershell
curl http://localhost:8000/api/health
```

正常例:

```json
{"ok":true,"storageDriver":"sqlite"}
```

`storageDriver: "json-fallback"` の場合は Python 側の `sqlite3` が使えていない可能性があります。

## frontend 初回セットアップ

Windows PowerShell では `npm.ps1` が Execution Policy で止まることがあるため、`npm.cmd` を使います。

```powershell
cd D:\ohanashi\frontend
npm.cmd install
npm.cmd run dev -- --host 0.0.0.0
```

補助スクリプト:

```powershell
powershell -ExecutionPolicy Bypass -File frontend\run_frontend.ps1
```

PC ブラウザ:

- `http://localhost:5173`

## backend 接続状態の見方

- `backend 接続 OK`: frontend から `/api/health` を取得できています
- `backend に接続できません`: backend が起動していないか、URL が違う可能性があります
- `保存状態: SQLite`: 正常です
- `保存状態: JSON fallback。Python の sqlite3 確認が必要です。`: SQLite が使えていません
- 確認時刻: frontend が最後に `/api/health` を取得した時刻です

## API ベース URL の上書き

既定の backend URL は `http://127.0.0.1:8000` です。必要なら `VITE_API_BASE_URL` で上書きできます。

例:

```powershell
$env:VITE_API_BASE_URL="http://192.168.1.20:8000"
npm.cmd run dev -- --host 0.0.0.0
```

`.env.local` は Git に入れないでください。

## スマホから使う手順

前提:

- backend も frontend も起動しておく
- frontend は `--host 0.0.0.0` 付きで起動する
- PC とスマホは同じ Wi-Fi に接続する

PC の IPv4 確認:

```powershell
ipconfig
```

スマホから開く URL:

```text
http://<PCのIPv4アドレス>:5173
```

例:

```text
http://192.168.1.20:5173
```

## Windows ファイアウォールで詰まるとき

次を確認してください。

- `node.exe` または `npm` の通信がブロックされていないか
- `5173` ポートの受信がブロックされていないか
- backend の `8000` ポートも PC 内で起動しているか
- 企業ネットワークやゲスト Wi-Fi で端末間通信が禁止されていないか

## トラブルシュート

`backend\.venv\Scripts\python.exe was not found`

- 原因: clone 直後で backend 仮想環境が未作成です
- 対応: `powershell -ExecutionPolicy Bypass -File backend\setup_backend.ps1`

`No module named uvicorn`

- 原因: `requirements.txt` が未インストールです
- 対応:

```powershell
.\backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

`ssl module in Python is not available`

- 原因: Python 実行環境の SSL DLL が壊れているか、Anaconda 環境の DLL 解決問題です
- 対応: 公式 Python 3.10 から 3.12 を入れ、その Python で venv を作り直してください

`ImportError: DLL load failed while importing _sqlite3`

- 原因: `sqlite3` の DLL 解決に失敗しています
- 対応: 公式 Python 3.10 から 3.12 を使うか、SQLite が使える Python で `backend/.venv` を作り直してください

`npm.ps1 を読み込めない`

- 原因: PowerShell の Execution Policy で `npm.ps1` がブロックされています
- 対応:

```powershell
cd frontend
npm.cmd install
npm.cmd run dev -- --host 0.0.0.0
```

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
- [ ] スマホから `http://<PCのIPv4アドレス>:5173` でアクセスできる
- [ ] 会話全文・音声・文字起こし全文ログが永続保存されない

## テスト

backend:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
pytest backend/tests -q
```

frontend:

```powershell
cd frontend
npm.cmd run build
```
