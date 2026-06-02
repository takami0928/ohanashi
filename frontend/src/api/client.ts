export type Settings = {
  toy_name: string;
  child_name: string;
  mode_chat_enabled: boolean;
  mode_adventure_enabled: boolean;
  mode_wordplay_enabled: boolean;
  mode_story_enabled: boolean;
  mode_sleepy_enabled: boolean;
  voice_enabled: boolean;
  speech_rate: number;
  energy: string;
  session_limit_minutes: number;
  daily_limit_minutes: number;
  max_turns: number;
  debug_mode: boolean;
};

export type MemoryCard = {
  id: string;
  category: string;
  key: string;
  value: string;
  scope: string;
  created_at: string;
  updated_at: string;
  expires_at: string | null;
};

export type DashboardPayload = {
  settings: Settings;
  usage: {
    todaySeconds: number;
    last7Days: Array<{ day: string; seconds: number; modes: Record<string, number> }>;
    modeTotals: Record<string, number>;
  };
  memories: MemoryCard[];
  storageDriver: string;
};

export type TurnResponse = {
  session_id: string;
  mode: string;
  safety_level: number;
  state_label: string;
  response_text: string;
  audio_base64: string | null;
  used_llm: boolean;
  used_asr: boolean;
  used_tts: boolean;
  debug?: Record<string, unknown>;
};

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    throw new Error(`API ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export const api = {
  bootstrap: () => request<DashboardPayload>("/api/bootstrap"),
  childTurn: (payload: Record<string, unknown>) =>
    request<TurnResponse>("/api/child/turn", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  devTurn: (payload: Record<string, unknown>) =>
    request<TurnResponse>("/api/dev/turn", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  saveSettings: (payload: Partial<Settings>) =>
    request<Settings>("/api/settings", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateMemory: (id: string, payload: Partial<MemoryCard>) =>
    request<MemoryCard>(`/api/memories/${id}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  deleteMemory: (id: string) =>
    request<{ ok: boolean }>(`/api/memories/${id}`, {
      method: "DELETE",
    }),
};

