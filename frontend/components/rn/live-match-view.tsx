"use client";

import { useState, useEffect, useCallback } from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  Image,
} from "react-native";
import { COLORS, type MatchState } from "@/lib/types";
import {
  API_BASE,
  fetchState,
  apiStartTimer,
  apiSetTeam,
  apiSetBreakdown,
  apiSaveRun,
  mapBoxDropFrontendToBackend,
} from "@/lib/api";

interface LiveMatchViewProps {
  backgroundNumber?: string;
  onTeamSet?: (team: string) => void;
}

export function LiveMatchView({ backgroundNumber = "8", onTeamSet }: LiveMatchViewProps) {
  const [state, setState] = useState<MatchState>({
    teamNumber: "3083",
    score: 51,
    timerSeconds: 0,
    isRunning: false,
    obstacleTouches: 0,
    completedUnder60: false,
    boxDrop: "none",
  });
  const [teamInput, setTeamInput] = useState("");
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  // Poll state from API (use mapped camelCase from lib/api)
  useEffect(() => {
    const poll = async () => {
      const next = await fetchState();
      if (next) setState(next);
    };
    const interval = setInterval(poll, 500);
    poll();
    return () => clearInterval(interval);
  }, []);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const handleStartTimer = async () => {
    const next = await apiStartTimer();
    if (next) setState(next);
    else setState((prev) => ({ ...prev, isRunning: !prev.isRunning }));
  };

  const handleSetTeam = async () => {
    if (!teamInput.trim()) return;
    const next = await apiSetTeam(teamInput.trim());
    const teamForDisplay = next?.teamNumber ?? teamInput.trim();
    if (next) {
      setState(next);
      onTeamSet?.(teamForDisplay.replace(/^Team\s*/i, "").trim() || teamForDisplay);
    } else {
      setState((prev) => ({ ...prev, teamNumber: teamInput.trim() }));
      onTeamSet?.(teamInput.trim());
    }
    setTeamInput("");
  };

  const handleObstacleTouch = async () => {
    const newTouches = state.obstacleTouches + 1;
    const next = await apiSetBreakdown({ obstacle_touches: newTouches });
    if (next) setState(next);
    else setState((prev) => ({ ...prev, obstacleTouches: newTouches }));
  };

  const handleToggleUnder60 = async () => {
    const newValue = !state.completedUnder60;
    const next = await apiSetBreakdown({ completed_under_60: newValue });
    if (next) setState(next);
    else setState((prev) => ({ ...prev, completedUnder60: newValue }));
  };

  const handleBoxDrop = async (value: "none" | "net" | "barge") => {
    const backendValue = mapBoxDropFrontendToBackend(value);
    const next = await apiSetBreakdown({ box_drop: backendValue });
    if (next) setState(next);
    else setState((prev) => ({ ...prev, boxDrop: value }));
  };

  const handleSaveRun = async () => {
    await apiSaveRun();
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

      {/* Main Content */}
      <View style={styles.mainContent}>
        {/* Left Side - Team Info & Score */}
        <View style={styles.leftPanel}>
          {/* Team Number Box (placeholder until mount to avoid hydration mismatch) */}
          <View style={styles.teamBox}>
            <Text style={styles.teamNumber} suppressHydrationWarning>
              {mounted ? state.teamNumber : "—"}
            </Text>
          </View>

          {/* Score */}
          <Text style={styles.scoreLabel}>SCORE</Text>
          <Text style={styles.score}>{state.score}</Text>

          {/* Timer */}
          <View style={styles.timerContainer}>
            <Text style={styles.timerLabel}>TIME</Text>
            <Text style={styles.timer}>{formatTime(state.timerSeconds)}</Text>
            <View
              style={[
                styles.statusIndicator,
                state.isRunning ? styles.statusRunning : styles.statusStopped,
              ]}
            />
          </View>
        </View>

        {/* Right Side - Video Stream */}
        <View style={styles.rightPanel}>
          <View style={styles.videoContainer}>
            <Image
              source={{ uri: `${API_BASE}/stream` }}
              style={styles.videoStream}
              resizeMode="cover"
            />
            <View style={styles.videoOverlay}>
              <Text style={styles.videoOverlayText}>LIVE FEED</Text>
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

      {/* Controls */}
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
          <TouchableOpacity
            style={[styles.button, styles.buttonPrimary]}
            onPress={handleStartTimer}
          >
            <Text style={styles.buttonText}>
              {state.isRunning ? "STOP" : "START"}
            </Text>
          </TouchableOpacity>
        </View>

        <View style={styles.controlRow}>
          <TouchableOpacity style={styles.button} onPress={handleObstacleTouch}>
            <Text style={styles.buttonText}>+ OBSTACLE</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[
              styles.button,
              state.completedUnder60 && styles.buttonActive,
            ]}
            onPress={handleToggleUnder60}
          >
            <Text style={styles.buttonText}>UNDER 60s</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.controlRow}>
          {(["none", "net", "barge"] as const).map((option) => (
            <TouchableOpacity
              key={option}
              style={[
                styles.button,
                styles.buttonSmall,
                state.boxDrop === option && styles.buttonActive,
              ]}
              onPress={() => handleBoxDrop(option)}
            >
              <Text style={styles.buttonText}>{option.toUpperCase()}</Text>
            </TouchableOpacity>
          ))}
          <TouchableOpacity
            style={[styles.button, styles.buttonSave]}
            onPress={handleSaveRun}
          >
            <Text style={styles.buttonText}>SAVE RUN</Text>
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
    flexDirection: "row",
    flex: 1,
    padding: 20,
    zIndex: 1,
  },
  leftPanel: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    paddingRight: 20,
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
  rightPanel: {
    flex: 1,
    paddingLeft: 20,
  },
  videoContainer: {
    flex: 1,
    backgroundColor: COLORS.darkBlue,
    borderRadius: 8,
    overflow: "hidden",
    borderWidth: 3,
    borderColor: COLORS.white,
  },
  videoStream: {
    width: "100%",
    height: "100%",
  },
  videoOverlay: {
    position: "absolute",
    top: 10,
    right: 10,
    backgroundColor: "#EF4444",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  videoOverlayText: {
    color: COLORS.white,
    fontSize: 12,
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
  buttonPrimary: {
    backgroundColor: COLORS.yellow,
  },
  buttonActive: {
    backgroundColor: COLORS.yellow,
  },
  buttonSmall: {
    paddingHorizontal: 16,
  },
  buttonSave: {
    backgroundColor: "#22C55E",
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
