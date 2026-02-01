"use client";

import { useState, useEffect, useRef } from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
} from "react-native";
import { COLORS, type MatchState } from "@/lib/types";
import {
  fetchState,
  apiSetTeam,
  apiStartTimer,
  apiStopTimer,
} from "@/lib/api";

interface LiveMatchViewProps {
  backgroundNumber?: string;
  onTeamSet?: (team: string) => void;
}

const initialMatchState: MatchState = {
  teamNumber: "—",
  score: 0,
  timerSeconds: 0,
  isRunning: false,
  obstacleTouches: 0,
  completedUnder60: false,
  boxDrop: "none",
};

export function LiveMatchView({ backgroundNumber = "8", onTeamSet }: LiveMatchViewProps) {
  const [state, setState] = useState<MatchState>(initialMatchState);
  const [teamInput, setTeamInput] = useState("");
  const [mounted, setMounted] = useState(false);
  const initialTeamSynced = useRef(false);

  useEffect(() => setMounted(true), []);

  // Poll state from API; sync team to parent once on first successful fetch
  useEffect(() => {
    const poll = async () => {
      const next = await fetchState();
      if (next) {
        setState(next);
        if (!initialTeamSynced.current && next.teamNumber) {
          const raw = next.teamNumber.replace(/^Team\s*/i, "").trim() || next.teamNumber;
          onTeamSet?.(raw);
          initialTeamSynced.current = true;
        }
      }
    };
    const interval = setInterval(poll, 500);
    poll();
    return () => clearInterval(interval);
  }, [onTeamSet]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const handleSetTeam = async () => {
    if (!teamInput.trim()) return;
    const raw = teamInput.trim();
    // Update display immediately (same variable as background + team box above score)
    onTeamSet?.(raw);
    setTeamInput("");
    // Optionally sync to backend
    const next = await apiSetTeam(raw);
    if (next) setState(next);
  };

  const handleStartTimer = async () => {
    const next = await apiStartTimer();
    if (next) setState(next);
  };

  const handleStopTimer = async () => {
    const next = await apiStopTimer();
    if (next) setState(next);
  };

  return (
    <View style={styles.container}>
      {/* Background Number Watermark (placeholder until mount to avoid hydration mismatch) */}
      <View style={styles.watermarkContainer}>
        <Text style={styles.watermarkNumber} suppressHydrationWarning>
          {mounted ? backgroundNumber : "—"}
        </Text>
      </View>

      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>UTRA MATCH</Text>
        <Text style={styles.headerSubtitle}>Round 1 - Match 1</Text>
      </View>

      {/* Main Content - centered score/timer block */}
      <View style={styles.mainContent}>
        <View style={styles.centerPanel}>
          {/* Team Number Box - same value as background (parent state) */}
          <View style={styles.teamBox}>
            <Text style={styles.teamNumber} suppressHydrationWarning>
              {mounted ? (backgroundNumber || "—") : "—"}
            </Text>
          </View>

          <Text style={styles.scoreLabel}>SCORE</Text>
          <Text style={styles.score}>{state.score}</Text>

          <View style={styles.timerContainer}>
            <Text style={styles.timerLabel}>TIME</Text>
            <Text style={styles.timer}>{formatTime(state.timerSeconds)}</Text>
            <View
              style={[
                styles.statusIndicator,
                state.isRunning ? styles.statusRunning : styles.statusStopped,
              ]}
            />
            <View style={styles.timerButtons}>
              <TouchableOpacity
                style={[styles.timerButton, styles.timerButtonStart]}
                onPress={handleStartTimer}
              >
                <Text style={styles.timerButtonText}>START MATCH</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.timerButton, styles.timerButtonEnd]}
                onPress={handleStopTimer}
              >
                <Text style={styles.timerButtonText}>END MATCH</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </View>

      {/* Score Breakdown Table */}
      <View style={styles.breakdownContainer}>
        <View style={styles.tableHeader}>
          <Text style={styles.tableHeaderText}>SCORE BREAKDOWN</Text>
        </View>
        <View style={[styles.tableRow, styles.tableRowLight]}>
          <Text style={styles.tableCellLabel}>Obstacle Touches</Text>
          <Text style={styles.tableCellValue}>{state.obstacleTouches}</Text>
        </View>
        <View style={[styles.tableRow, styles.tableRowDark]}>
          <Text style={styles.tableCellLabel}>Completed Under 60s</Text>
          <Text style={styles.tableCellValue}>
            {state.completedUnder60 ? "YES" : "NO"}
          </Text>
        </View>
        <View style={[styles.tableRow, styles.tableRowLight]}>
          <Text style={styles.tableCellLabel}>Box Drop</Text>
          <Text style={styles.tableCellValue}>
            {state.boxDrop.toUpperCase()}
          </Text>
        </View>
      </View>

      {/* Set team only */}
      <View style={styles.controlsContainer}>
        <View style={styles.controlRow}>
          <TextInput
            style={styles.input}
            placeholder="Team #"
            placeholderTextColor="#666"
            value={teamInput}
            onChangeText={setTeamInput}
            keyboardType="number-pad"
          />
          <TouchableOpacity style={styles.button} onPress={handleSetTeam}>
            <Text style={styles.buttonText}>SET TEAM</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Footer */}
      <View style={styles.footer}>
        <Text style={styles.footerText}>Match Results Powered By UTRA</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.primaryBlue,
    position: "relative",
  },
  watermarkContainer: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    justifyContent: "center",
    alignItems: "center",
    zIndex: 0,
  },
  watermarkNumber: {
    fontSize: 500,
    fontWeight: "900",
    color: COLORS.watermarkBlue,
    opacity: 0.3,
  },
  header: {
    backgroundColor: COLORS.headerDark,
    paddingVertical: 12,
    paddingHorizontal: 20,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    zIndex: 1,
  },
  headerTitle: {
    color: COLORS.white,
    fontSize: 24,
    fontWeight: "bold",
    letterSpacing: 2,
  },
  headerSubtitle: {
    color: COLORS.white,
    fontSize: 18,
    fontWeight: "600",
  },
  mainContent: {
    flex: 1,
    padding: 20,
    zIndex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  centerPanel: {
    alignItems: "center",
    justifyContent: "center",
  },
  teamBox: {
    backgroundColor: COLORS.teamBoxBlue,
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 4,
    marginBottom: 20,
    borderWidth: 2,
    borderColor: COLORS.white,
  },
  teamNumber: {
    color: COLORS.white,
    fontSize: 32,
    fontWeight: "bold",
  },
  scoreLabel: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: "600",
    marginBottom: 4,
    opacity: 0.8,
  },
  score: {
    color: COLORS.white,
    fontSize: 120,
    fontWeight: "900",
    lineHeight: 120,
  },
  timerContainer: {
    alignItems: "center",
    marginTop: 20,
  },
  timerLabel: {
    color: COLORS.white,
    fontSize: 14,
    fontWeight: "600",
    opacity: 0.8,
  },
  timer: {
    color: COLORS.white,
    fontSize: 48,
    fontWeight: "bold",
    fontVariant: ["tabular-nums"],
  },
  statusIndicator: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginTop: 8,
  },
  statusRunning: {
    backgroundColor: "#22C55E",
  },
  statusStopped: {
    backgroundColor: "#EF4444",
  },
  timerButtons: {
    flexDirection: "row",
    gap: 12,
    marginTop: 16,
  },
  timerButton: {
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 4,
    borderWidth: 2,
    borderColor: COLORS.white,
  },
  timerButtonStart: {
    backgroundColor: "#22C55E",
  },
  timerButtonEnd: {
    backgroundColor: "#EF4444",
  },
  timerButtonText: {
    color: COLORS.white,
    fontSize: 14,
    fontWeight: "bold",
  },
  breakdownContainer: {
    marginHorizontal: 20,
    marginBottom: 10,
    borderRadius: 4,
    overflow: "hidden",
    zIndex: 1,
  },
  tableHeader: {
    backgroundColor: COLORS.headerDark,
    paddingVertical: 10,
    paddingHorizontal: 16,
  },
  tableHeaderText: {
    color: COLORS.white,
    fontSize: 14,
    fontWeight: "bold",
    textAlign: "center",
  },
  tableRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 12,
    paddingHorizontal: 16,
  },
  tableRowLight: {
    backgroundColor: COLORS.tableRowLight,
  },
  tableRowDark: {
    backgroundColor: COLORS.tableRowDark,
  },
  tableCellLabel: {
    color: COLORS.darkText,
    fontSize: 16,
    fontWeight: "600",
  },
  tableCellValue: {
    color: COLORS.darkText,
    fontSize: 16,
    fontWeight: "bold",
  },
  controlsContainer: {
    padding: 20,
    gap: 10,
    zIndex: 1,
  },
  controlRow: {
    flexDirection: "row",
    gap: 10,
    justifyContent: "center",
  },
  input: {
    backgroundColor: COLORS.white,
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 4,
    fontSize: 16,
    minWidth: 100,
    color: COLORS.darkText,
  },
  button: {
    backgroundColor: COLORS.darkBlue,
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 4,
    borderWidth: 2,
    borderColor: COLORS.white,
  },
  buttonText: {
    color: COLORS.white,
    fontSize: 14,
    fontWeight: "bold",
    textAlign: "center",
  },
  footer: {
    backgroundColor: COLORS.headerDark,
    paddingVertical: 12,
    alignItems: "center",
    zIndex: 1,
  },
  footerText: {
    color: COLORS.white,
    fontSize: 14,
    fontWeight: "600",
  },
});
