import { startTransition, useEffect, useState } from "react";

import { api, type DashboardPayload, type HealthState, type Settings } from "./api/client";
import { ChildScreen } from "./pages/ChildScreen";
import { DevScreen } from "./pages/DevScreen";
import { ParentScreen } from "./pages/ParentScreen";

type Page = "child" | "parent" | "dev";

const INITIAL_HEALTH: HealthState = {
  status: "checking",
  storageDriver: null,
  checkedAt: null,
  message: "backend を確認しています。",
};

export default function App() {
  const [page, setPage] = useState<Page>("child");
  const [dashboard, setDashboard] = useState<DashboardPayload | null>(null);
  const [health, setHealth] = useState<HealthState>(INITIAL_HEALTH);
  const [error, setError] = useState("");

  useEffect(() => {
    void refreshApp();
  }, []);

  async function refreshApp() {
    await Promise.all([refreshDashboard(), refreshHealth()]);
  }

  async function refreshDashboard() {
    try {
      const next = await api.bootstrap();
      startTransition(() => {
        setDashboard(next);
        setError("");
      });
    } catch {
      setError("backend に接続できません。README の手順でローカルサーバーを起動してください。");
    }
  }

  async function refreshHealth() {
    setHealth((current) => ({
      ...current,
      status: current.checkedAt ? current.status : "checking",
      message: current.checkedAt ? current.message : "backend を確認しています。",
    }));

    try {
      const next = await api.health();
      setHealth({
        status: "ok",
        storageDriver: next.storageDriver,
        checkedAt: new Date().toISOString(),
        message: "backend 接続 OK",
      });
    } catch {
      setHealth({
        status: "offline",
        storageDriver: null,
        checkedAt: new Date().toISOString(),
        message: "backend に接続できません。backend を起動してください。",
      });
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
      <header className={page === "child" ? "topbar topbar--child" : "topbar"}>
        <div>
          <p className="eyebrow">Local Plush Brain MVP</p>
          <h1>しゃべるぬいぐるみの脳</h1>
        </div>
        {page !== "child" ? (
          <nav className="tabbar" aria-label="ページ切り替え">
            <button className={tabClass(page, "child")} onClick={() => setPage("child")}>
              子ども
            </button>
            <button className={tabClass(page, "parent")} onClick={() => setPage("parent")}>
              親
            </button>
            <button className={tabClass(page, "dev")} onClick={() => setPage("dev")}>
              開発
            </button>
          </nav>
        ) : null}
      </header>

      {!dashboard ? (
        <section className="panel">
          <p className="eyebrow">接続確認</p>
          <h2>つなぎ中</h2>
          <p>{error || "ローカルサーバーと設定を読み込んでいます。"}</p>
        </section>
      ) : null}

      {dashboard && page === "child" ? (
        <ChildScreen
          settings={dashboard.settings}
          health={health}
          onParentOpen={() => setPage("parent")}
          onDevOpen={() => setPage("dev")}
        />
      ) : null}
      {dashboard && page === "parent" ? (
        <ParentScreen
          dashboard={dashboard}
          health={health}
          onRefreshHealth={refreshHealth}
          onSettingsUpdated={updateSettings}
          onDashboardRefresh={refreshDashboard}
        />
      ) : null}
      {dashboard && page === "dev" ? (
        <DevScreen health={health} onRefreshHealth={refreshHealth} onDashboardRefresh={refreshDashboard} />
      ) : null}
    </main>
  );
}

function tabClass(current: Page, target: Page) {
  return current === target ? "tabbar__button active" : "tabbar__button";
}
