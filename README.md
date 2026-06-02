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

推奨:

```bash
py -3.8 -m pip install -r backend/requirements.txt
py -3.8 -m uvicorn backend.app.main:app --reload
```

この作業環境のように FastAPI / sqlite3 がそろっていない場合のフォールバック:

```bash
py -3.8 -m backend.app.main
```

### 2. フロントエンド

```bash
cd frontend
npm install
npm run dev
```

### 3. アクセス

- フロント: `http://127.0.0.1:5173`
- バックエンド: `http://127.0.0.1:8000`

## テスト

この環境では pytest の自動ロードプラグインがハングしたため、以下で実行します。

```bash
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
py -3.8 -m pytest backend/tests -q

## SQLite の現状

この環境の `py -3.8` では、次のエラーで `sqlite3` が未復旧です。

```text
ImportError: DLL load failed while importing _sqlite3: 指定されたモジュールが見つかりません。
```

そのため、現在の `/api/health` は `storageDriver: "json-fallback"` を返します。
```

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
