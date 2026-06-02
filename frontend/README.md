# Frontend

スマホ Web/PWA 側の画面です。子ども画面、親画面、開発画面を持ちます。

## 画面の役割

- 子ども画面: 大きな「おはなしする」ボタンでぬいぐるみに話しかける画面です。会話履歴一覧は表示しません。
- 親画面: 利用時間、使用モード、記憶カード、設定、接続状態を確認する画面です。会話全文は表示しません。
- 開発画面: テキスト入力で orchestrator を試し、返答方式や安全判定の確認をする画面です。表示内容は保存しません。

## 起動

PowerShell では `npm.ps1` がブロックされることがあるため、Windows では `npm.cmd` を推奨します。

```powershell
cd frontend
npm.cmd install
npm.cmd run dev -- --host 0.0.0.0
```

補助スクリプト:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_frontend.ps1
```

PC ブラウザ:

- `http://localhost:5173`

## backend 接続状態

親画面と開発画面で次を確認できます。

- backend 接続 OK / backend 未接続
- `storageDriver`
- `/api/health` の取得時刻

表示の意味:

- `保存状態: SQLite`: 正常です
- `保存状態: JSON fallback。Python の sqlite3 確認が必要です。`: backend の SQLite が使えていません

## API ベース URL

既定値:

- `http://127.0.0.1:8000`

必要なら `VITE_API_BASE_URL` で上書きできます。

```powershell
$env:VITE_API_BASE_URL="http://192.168.1.20:8000"
npm.cmd run dev -- --host 0.0.0.0
```

互換のため `VITE_API_BASE` でも動きますが、新規設定では `VITE_API_BASE_URL` を推奨します。

## スマホから使うとき

- backend も frontend も起動しておく
- frontend は `--host 0.0.0.0` 付きで起動する
- PC とスマホは同じ Wi-Fi に接続する
- Windows ファイアウォールで `5173` と `8000` がブロックされていないことを確認する

アクセス例:

```text
http://192.168.1.20:5173
```

## ビルド

```powershell
npm.cmd run build
```

## 重要な非保存方針

- 会話全文は保存しません
- 音声データは保存しません
- 文字起こし全文ログは保存しません
