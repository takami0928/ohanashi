# Frontend

スマホWeb/PWA向けのフロントエンドです。

## 画面

- 子ども画面: 大きな会話ボタン、状態表示、最新の返答だけ表示
- 親画面: 利用状況、設定、記憶カード
- 開発画面: テキスト入力フォールバック、その場だけのデバッグ表示

## 起動

```bash
npm install
npm run dev
```

同一 Wi-Fi のスマホから開く場合:

```bash
npm run dev -- --host 0.0.0.0
```

## ビルド

```bash
npm run build
```

## API 接続先

デフォルトは `http://127.0.0.1:8000` です。

スマホから確認するときは、frontend は `0.0.0.0` で listen させ、スマホでは `http://<PCのIPv4アドレス>:5173` を開きます。

変更する場合:

```bash
VITE_API_BASE=http://127.0.0.1:8000
```
