import type { DashboardPayload, MemoryCard, Settings } from "../api/client";
import { api } from "../api/client";

type ParentScreenProps = {
  dashboard: DashboardPayload;
  onSettingsUpdated: (settings: Settings) => void;
  onDashboardRefresh: () => Promise<void>;
};

export function ParentScreen({ dashboard, onSettingsUpdated, onDashboardRefresh }: ParentScreenProps) {
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
        <section className="panel">
          <p className="eyebrow">利用状況</p>
          <h2>今日の利用</h2>
          <strong className="metric">{Math.round(dashboard.usage.todaySeconds / 60)} 分</strong>
          <ul className="usage-list">
            {dashboard.usage.last7Days.map((item) => (
              <li key={item.day}>
                <span>{item.day}</span>
                <span>{Math.round(item.seconds / 60)}分</span>
              </li>
            ))}
          </ul>
        </section>

        <section className="panel">
          <p className="eyebrow">ぬいぐるみ設定</p>
          <label>
            ぬいぐるみの名前
            <input
              defaultValue={settings.toy_name}
              onBlur={(event) => saveField("toy_name", event.target.value)}
            />
          </label>
          <label>
            子どもの呼び名
            <input
              defaultValue={settings.child_name}
              onBlur={(event) => saveField("child_name", event.target.value)}
            />
          </label>
          <label>
            話す速さ
            <input
              type="range"
              min="0.7"
              max="1.2"
              step="0.05"
              defaultValue={settings.speech_rate}
              onChange={(event) => saveField("speech_rate", Number(event.target.value))}
            />
          </label>
          <label>
            元気度
            <select defaultValue={settings.energy} onChange={(event) => saveField("energy", event.target.value)}>
              <option value="gentle">やさしい</option>
              <option value="bouncy">げんき</option>
              <option value="sleepy">ねむねむ</option>
            </select>
          </label>
          <label className="toggle">
            <input
              type="checkbox"
              checked={settings.voice_enabled}
              onChange={(event) => saveField("voice_enabled", event.target.checked)}
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
                onChange={(event) => saveField(item.key, event.target.checked)}
              />
              {item.label}
            </label>
          ))}
        </section>

        <section className="panel">
          <p className="eyebrow">利用時間制限</p>
          <label>
            1回の会話上限（分）
            <input
              type="number"
              min="5"
              max="10"
              defaultValue={settings.session_limit_minutes}
              onBlur={(event) => saveField("session_limit_minutes", Number(event.target.value))}
            />
          </label>
          <label>
            1日の合計上限（分）
            <input
              type="number"
              min="10"
              max="40"
              defaultValue={settings.daily_limit_minutes}
              onBlur={(event) => saveField("daily_limit_minutes", Number(event.target.value))}
            />
          </label>
          <label>
            往復数上限
            <input
              type="number"
              min="5"
              max="8"
              defaultValue={settings.max_turns}
              onBlur={(event) => saveField("max_turns", Number(event.target.value))}
            />
          </label>
        </section>

        <section className="panel panel--wide">
          <p className="eyebrow">記憶カード</p>
          <p className="helper-text">
            会話全文は保存しません。保存対象は呼び名、好きなもの、遊び、抽象化した最近の話題だけです。
          </p>
          <div className="memory-list">
            {dashboard.memories.map((card) => (
              <article className="memory-card" key={card.id}>
                <small>{card.category}</small>
                <input
                  defaultValue={card.value}
                  onBlur={(event) => saveMemory({ ...card, value: event.target.value })}
                />
                <button className="secondary-button" onClick={() => deleteMemory(card.id)}>
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
            <li>親画面でも危険発話の原文は見えません。</li>
          </ul>
        </section>
      </div>
    </section>
  );
}

const modeToggles: Array<{ key: keyof Settings; label: string }> = [
  { key: "mode_chat_enabled", label: "おしゃべり" },
  { key: "mode_adventure_enabled", label: "ごっこ冒険" },
  { key: "mode_wordplay_enabled", label: "ことば遊び" },
  { key: "mode_story_enabled", label: "お話づくり" },
  { key: "mode_sleepy_enabled", label: "ねむねむ" },
];
