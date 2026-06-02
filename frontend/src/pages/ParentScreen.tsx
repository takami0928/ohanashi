import { api, type DashboardPayload, type HealthState, type MemoryCard, type Settings } from "../api/client";

type ParentScreenProps = {
  dashboard: DashboardPayload;
  health: HealthState;
  onRefreshHealth: () => Promise<void>;
  onSettingsUpdated: (settings: Settings) => void;
  onDashboardRefresh: () => Promise<void>;
};

export function ParentScreen({
  dashboard,
  health,
  onRefreshHealth,
  onSettingsUpdated,
  onDashboardRefresh,
}: ParentScreenProps) {
  const settings = dashboard.settings;

  async function saveField(key: keyof Settings, value: string | boolean | number) {
    const next = await api.saveSettings({ [key]: value });
    onSettingsUpdated(next);
    await onDashboardRefresh();
  }

  async function saveMemory(card: MemoryCard) {
    await api.updateMemory(card.id, card);
    await onDashboardRefresh();
  }

  async function deleteMemory(cardId: string) {
    await api.deleteMemory(cardId);
    await onDashboardRefresh();
  }

  return (
    <section className="parent-screen">
      <div className="panel-grid">
        <section className="panel panel--wide">
          <p className="eyebrow">親画面について</p>
          <h2>見られるのは利用状況と設定だけです</h2>
          <p className="helper-text">
            このMVPは会話全文・音声・文字起こし全文ログを保存しません。親画面では利用状況、設定、記憶カードのみ確認できます。
          </p>
        </section>

        <section className="panel">
          <p className="eyebrow">接続状態</p>
          <h2>backend の状態</h2>
          <p className={health.status === "ok" ? "status-inline status-inline--ok" : "status-inline status-inline--warn"}>
            {health.message}
          </p>
          <p className="helper-text">{storageMessage(health.storageDriver ?? dashboard.storageDriver)}</p>
          <p className="helper-text">確認時刻: {formatCheckedAt(health.checkedAt)}</p>
          <button className="secondary-button" onClick={() => void onRefreshHealth()}>
            health を更新
          </button>
        </section>

        <section className="panel">
          <p className="eyebrow">利用状況</p>
          <h2>今日の利用</h2>
          <strong className="metric">{Math.round(dashboard.usage.todaySeconds / 60)} 分</strong>
          <ul className="usage-list">
            {dashboard.usage.last7Days.map((item) => (
              <li key={item.day}>
                <span>{item.day}</span>
                <span>{Math.round(item.seconds / 60)} 分</span>
              </li>
            ))}
          </ul>
        </section>

        <section className="panel">
          <p className="eyebrow">使用モード</p>
          <h2>過去7日で使った遊び</h2>
          <ul className="plain-list">
            {Object.entries(dashboard.usage.modeTotals).map(([mode, count]) => (
              <li key={mode}>
                {modeLabel(mode)}: {count} 回
              </li>
            ))}
          </ul>
        </section>

        <section className="panel">
          <p className="eyebrow">ぬいぐるみ設定</p>
          <label>
            ぬいぐるみの名前
            <input defaultValue={settings.toy_name} onBlur={(event) => void saveField("toy_name", event.target.value)} />
          </label>
          <label>
            子どもの呼び名
            <input defaultValue={settings.child_name} onBlur={(event) => void saveField("child_name", event.target.value)} />
          </label>
          <label>
            話す速さ
            <input
              type="range"
              min="0.7"
              max="1.2"
              step="0.05"
              defaultValue={settings.speech_rate}
              onChange={(event) => void saveField("speech_rate", Number(event.target.value))}
            />
          </label>
          <label>
            元気度
            <select defaultValue={settings.energy} onChange={(event) => void saveField("energy", event.target.value)}>
              <option value="gentle">やさしい</option>
              <option value="bouncy">げんき</option>
              <option value="sleepy">ねむねむ</option>
            </select>
          </label>
          <label className="toggle">
            <input
              type="checkbox"
              checked={settings.voice_enabled}
              onChange={(event) => void saveField("voice_enabled", event.target.checked)}
            />
            音声ON
          </label>
        </section>

        <section className="panel">
          <p className="eyebrow">モード設定</p>
          {modeToggles.map((item) => (
            <label className="toggle" key={item.key}>
              <input
                type="checkbox"
                checked={Boolean(settings[item.key])}
                onChange={(event) => void saveField(item.key, event.target.checked)}
              />
              {item.label}
            </label>
          ))}
        </section>

        <section className="panel">
          <p className="eyebrow">利用時間制限</p>
          <label>
            1回の会話時間の目安
            <input
              type="number"
              min="5"
              max="10"
              defaultValue={settings.session_limit_minutes}
              onBlur={(event) => void saveField("session_limit_minutes", Number(event.target.value))}
            />
          </label>
          <label>
            1日の利用時間の目安
            <input
              type="number"
              min="10"
              max="40"
              defaultValue={settings.daily_limit_minutes}
              onBlur={(event) => void saveField("daily_limit_minutes", Number(event.target.value))}
            />
          </label>
          <label>
            最大往復数
            <input
              type="number"
              min="5"
              max="8"
              defaultValue={settings.max_turns}
              onBlur={(event) => void saveField("max_turns", Number(event.target.value))}
            />
          </label>
        </section>

        <section className="panel panel--wide">
          <p className="eyebrow">記憶カード</p>
          <p className="helper-text">好きなものや軽い話題だけを保存します。困りごとや秘密の内容は保存しません。</p>
          <div className="memory-list">
            {dashboard.memories.map((card) => (
              <article className="memory-card" key={card.id}>
                <small>
                  {card.category} / {card.key}
                </small>
                <input defaultValue={card.value} onBlur={(event) => void saveMemory({ ...card, value: event.target.value })} />
                <button className="secondary-button" onClick={() => void deleteMemory(card.id)}>
                  削除
                </button>
              </article>
            ))}
            {!dashboard.memories.length ? <p>まだ記憶カードはありません。</p> : null}
          </div>
        </section>

        <section className="panel">
          <p className="eyebrow">安全方針</p>
          <ul className="plain-list">
            <li>危険・秘密・薬・個人情報は固定テンプレートで返します。</li>
            <li>会話全文、音声、文字起こし全文ログは保存しません。</li>
            <li>親画面では利用状況、設定、記憶カードだけを確認できます。</li>
          </ul>
        </section>
      </div>
    </section>
  );
}

function formatCheckedAt(value: string | null) {
  if (!value) {
    return "未取得";
  }
  return new Date(value).toLocaleTimeString("ja-JP", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function storageMessage(driver: string) {
  if (driver === "sqlite") {
    return "保存状態: SQLite";
  }
  if (driver === "json-fallback") {
    return "保存状態: JSON fallback。Python の sqlite3 確認が必要です。";
  }
  return `保存状態: ${driver}`;
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

const modeToggles: Array<{ key: keyof Settings; label: string }> = [
  { key: "mode_chat_enabled", label: "おしゃべり" },
  { key: "mode_adventure_enabled", label: "ごっこ冒険" },
  { key: "mode_wordplay_enabled", label: "ことば遊び" },
  { key: "mode_story_enabled", label: "お話づくり" },
  { key: "mode_sleepy_enabled", label: "ねむねむ" },
];
