/**
 * API client: maps backend (FastAPI) response to frontend types.
 * Backend: snake_case, box_drop_1, box_drop_2 (fully_in|edge_touching|less_than_half_out|mostly_out)
 * Frontend: camelCase, boxDrop1, boxDrop2 (fullyIn|edgeTouching|lessThanHalfOut|mostlyOut|none)
 */

import type { MatchState, LeaderboardEntry, BoxDropRating } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export { API_BASE };

export interface BackendState {
  team_number?: string;
  team_display?: string;
  score_total?: number;
  t_elapsed_s?: number;
  timer_running?: boolean;
  score_breakdown?: { obstacles?: number; completed_under_60?: number; box_drop?: number };
  obstacle_touches?: number;
  completed_under_60?: boolean;
  box_drop_1?: string | null;
  box_drop_2?: string | null;
}

function mapBoxDropBackendToFrontend(value: string | null | undefined): BoxDropRating {
  if (value === "fully_in") return "fullyIn";
  if (value === "edge_touching" || value === "partially_touching") return "edgeTouching";
  if (value === "less_than_half_out") return "lessThanHalfOut";
  if (value === "mostly_out") return "mostlyOut";
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
    boxDrop1: mapBoxDropBackendToFrontend(data.box_drop_1),
    boxDrop2: mapBoxDropBackendToFrontend(data.box_drop_2),
    scoreBreakdown: bd
      ? {
          obstacles: bd.obstacles ?? 0,
          completedUnder60: bd.completed_under_60 ?? 0,
          boxDrop: bd.box_drop ?? 0,
        }
      : undefined,
  };
}

export function mapBoxDropFrontendToBackend(value: BoxDropRating): string | null {
  if (value === "none") return null;
  if (value === "fullyIn") return "fully_in";
  if (value === "edgeTouching") return "edge_touching";
  if (value === "lessThanHalfOut") return "less_than_half_out";
  if (value === "mostlyOut") return "mostly_out";
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
      score_breakdown?: { obstacles?: number; completed_under_60?: number; box_drop?: number };
      obstacle_touches?: number;
      completed_under_60?: boolean;
      box_drop_1?: string | null;
      box_drop_2?: string | null;
    }> = await res.json();
    return data.map((row, i) => ({
      rank: i + 1,
      team: row.team_display ?? row.team_number ?? "—",
      score: row.score_total ?? 0,
      time: formatTime(row.t_elapsed_s ?? 0),
      obstacleTouches: row.obstacle_touches ?? 0,
      completedUnder60: row.completed_under_60 ?? false,
      boxDrop1: mapBoxDropBackendToFrontend(row.box_drop_1),
      boxDrop2: mapBoxDropBackendToFrontend(row.box_drop_2),
      boxDropTotal: row.score_breakdown?.box_drop ?? 0,
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

export async function apiStopTimer(): Promise<MatchState | null> {
  try {
    const res = await fetch(`${API_BASE}/api/timer/stop`, { method: "POST" });
    if (!res.ok) return null;
    const data: BackendState = await res.json();
    return mapBackendStateToMatchState(data);
  } catch {
    return null;
  }
}

export async function apiResetTimer(): Promise<MatchState | null> {
  try {
    const res = await fetch(`${API_BASE}/api/timer/reset`, { method: "POST" });
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
  box_drop_1?: string | null;
  box_drop_2?: string | null;
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

/** Event dispatched when a run is saved so Leaderboard can refetch. */
export const LEADERBOARD_SAVED_EVENT = "leaderboard-saved";

export async function apiSaveRun(): Promise<LeaderboardEntry[] | null> {
  try {
    const res = await fetch(`${API_BASE}/api/test/save_run`, { method: "POST" });
    if (!res.ok) return null;
    const data = await res.json();
    const list = Array.isArray(data.leaderboard) ? data.leaderboard : [];
    const entries: LeaderboardEntry[] = list.map(
      (row: { team_display?: string; team_number?: string; score_total?: number; t_elapsed_s?: number; obstacle_touches?: number; completed_under_60?: boolean; box_drop_1?: string | null; box_drop_2?: string | null; score_breakdown?: { box_drop?: number } },
       i: number) => ({
        rank: i + 1,
        team: row.team_display ?? row.team_number ?? "—",
        score: row.score_total ?? 0,
        time: formatTime(row.t_elapsed_s ?? 0),
        obstacleTouches: row.obstacle_touches ?? 0,
        completedUnder60: row.completed_under_60 ?? false,
        boxDrop1: mapBoxDropBackendToFrontend(row.box_drop_1),
        boxDrop2: mapBoxDropBackendToFrontend(row.box_drop_2),
        boxDropTotal: row.score_breakdown?.box_drop ?? 0,
      })
    );
    if (typeof window !== "undefined") window.dispatchEvent(new CustomEvent(LEADERBOARD_SAVED_EVENT, { detail: entries }));
    return entries;
  } catch {
    return null;
  }
}

export async function apiCommentaryPush(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/api/commentary/push`, { method: "POST" });
    if (!res.ok) return false;
    const data = await res.json();
    return data.pushed === true;
  } catch {
    return false;
  }
}
