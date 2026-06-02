import { startTransition, useEffect, useState } from "react";

import { api, type DashboardPayload, type Settings } from "./api/client";
import { ChildScreen } from "./pages/ChildScreen";
import { DevScreen } from "./pages/DevScreen";
import { ParentScreen } from "./pages/ParentScreen";

type Page = "child" | "parent" | "dev";

export default function App() {
  const [page, setPage] = useState<Page>("child");
  const [dashboard, setDashboard] = useState<DashboardPayload | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    void refreshDashboard();
  }, []);

  async function refreshDashboard() {
    try {
      const next = await api.bootstrap();
      startTransition(() => {
        setDashboard(next);
        setError("");
      });
    } catch {
      setError("バックエンドに接続できません。README の手順でローカルサーバーを起動してください。");
    }
  }

  function updateSettings(settings: Settings) {
    if (!dashboard) {
      return;
    }
    setDashboard({ ...dashboard, settings });
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Local Plush Brain MVP</p>
          <h1>しゃべるぬいぐるみの脳</h1>
        </div>
        <nav className="tabbar">
          <button className={page === "child" ? "tabbar__button active" : "tabbar__button"} onClick={() => setPage("child")}>
            子ども
          </button>
          <button className={page === "parent" ? "tabbar__button active" : "tabbar__button"} onClick={() => setPage("parent")}>
            親
          </button>
          <button className={page === "dev" ? "tabbar__button active" : "tabbar__button"} onClick={() => setPage("dev")}>
            開発
          </button>
        </nav>
      </header>

      {!dashboard ? (
        <section className="panel">
          <p className="eyebrow">状態</p>
          <h2>つなぎ中</h2>
          <p>{error || "ローカルサーバーと設定を読み込んでいます。"}</p>
        </section>
      ) : null}

      {dashboard && page === "child" ? <ChildScreen settings={dashboard.settings} /> : null}
      {dashboard && page === "parent" ? (
        <ParentScreen dashboard={dashboard} onSettingsUpdated={updateSettings} onDashboardRefresh={refreshDashboard} />
      ) : null}
      {dashboard && page === "dev" ? <DevScreen storageDriver={dashboard.storageDriver} /> : null}
    </main>
  );
}

