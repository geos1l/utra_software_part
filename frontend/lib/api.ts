/**
 * API client: maps backend (FastAPI) response to frontend types.
 * Backend: snake_case, team_number, t_elapsed_s, score_breakdown, box_drop "fully_in"|"partially_touching"|"mostly_out"|null
 * Frontend: camelCase, teamNumber, timerSeconds, boxDrop "none"|"net"|"barge"
 */

import type { MatchState, LeaderboardEntry } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export { API_BASE };

export interface BackendState {
  team_number?: string;
  team_display?: string;
  score_total?: number;
  t_elapsed_s?: number;
  timer_running?: boolean;
  score_breakdown?: { obstacle?: number; completed_under_60?: number; box_drop?: number };
  obstacle_touches?: number;
  completed_under_60?: boolean;
  box_drop?: string | null;
}

function mapBoxDropBackendToFrontend(value: string | null | undefined): "none" | "net" | "barge" {
  if (value === "fully_in" || value === "partially_touching") return "net";
  if (value === "mostly_out") return "barge";
  return "none";
}

export function mapBackendStateToMatchState(data: BackendState): MatchState {
  const bd = data.score_breakdown;
  return {
    teamNumber: data.team_display ?? data.team_number ?? "—",
    score: data.score_total ?? 0,
    timerSeconds: data.t_elapsed_s ?? 0,
    isRunning: data.timer_running ?? false,
    obstacleTouches: data.obstacle_touches ?? 0,
    completedUnder60: data.completed_under_60 ?? false,
    boxDrop: mapBoxDropBackendToFrontend(data.box_drop),
    scoreBreakdown: bd
      ? {
          obstacle: bd.obstacle ?? 0,
          completedUnder60: bd.completed_under_60 ?? 0,
          boxDrop: bd.box_drop ?? 0,
        }
      : undefined,
  };
}

export function mapBoxDropFrontendToBackend(value: "none" | "net" | "barge"): string | null {
  if (value === "none") return null;
  if (value === "net") return "fully_in";
  if (value === "barge") return "mostly_out";
  return null;
}

export async function fetchState(): Promise<MatchState | null> {
  try {
    const res = await fetch(`${API_BASE}/api/state`);
    if (!res.ok) return null;
    const data: BackendState = await res.json();
    return mapBackendStateToMatchState(data);
  } catch {
    return null;
  }
}

export async function fetchLeaderboard(): Promise<LeaderboardEntry[]> {
  try {
    const res = await fetch(`${API_BASE}/api/leaderboard`);
    if (!res.ok) return [];
    const data: Array<{
      team_number?: string;
      team_display?: string;
      score_total?: number;
      t_elapsed_s?: number;
      score_breakdown?: { obstacle?: number; completed_under_60?: number; box_drop?: number };
      obstacle_touches?: number;
      completed_under_60?: boolean;
      box_drop?: string | null;
    }> = await res.json();
    return data.map((row, i) => ({
      rank: i + 1,
      team: row.team_display ?? row.team_number ?? "—",
      score: row.score_total ?? 0,
      time: formatTime(row.t_elapsed_s ?? 0),
      obstacleTouches: row.score_breakdown?.obstacle ?? row.obstacle_touches ?? 0,
      completedUnder60: row.completed_under_60 ?? false,
      boxDrop: mapBoxDropBackendToFrontend(row.box_drop),
    }));
  } catch {
    return [];
  }
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}

export async function apiStartTimer(): Promise<MatchState | null> {
  try {
    const res = await fetch(`${API_BASE}/api/timer/start`, { method: "POST" });
    if (!res.ok) return null;
    const data: BackendState = await res.json();
    return mapBackendStateToMatchState(data);
  } catch {
    return null;
  }
}

export async function apiSetTeam(team: string): Promise<MatchState | null> {
  try {
    const res = await fetch(`${API_BASE}/api/set_team`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ team_number: team, team }), // backend accepts both
    });
    if (!res.ok) return null;
    const data: BackendState = await res.json();
    return mapBackendStateToMatchState(data);
  } catch {
    return null;
  }
}

export async function apiSetBreakdown(payload: {
  obstacle_touches?: number;
  completed_under_60?: boolean;
  box_drop?: string | null;
}): Promise<MatchState | null> {
  try {
    const res = await fetch(`${API_BASE}/api/test/set_breakdown`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) return null;
    const data: BackendState = await res.json();
    return mapBackendStateToMatchState(data);
  } catch {
    return null;
  }
}

export async function apiSaveRun(): Promise<void> {
  try {
    await fetch(`${API_BASE}/api/test/save_run`, { method: "POST" });
  } catch {
    // ignore
  }
}
