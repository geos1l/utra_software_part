"use client";

import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Dimensions,
} from "react-native";
import { useState, useEffect, useCallback } from "react";
import { COLORS, type LeaderboardEntry } from "@/lib/types";
import { fetchLeaderboard, LEADERBOARD_SAVED_EVENT } from "@/lib/api";

const { width: SCREEN_WIDTH } = Dimensions.get("window");

interface LeaderboardViewProps {
  backgroundNumber?: string;
}

export function LeaderboardView({ backgroundNumber = "1" }: LeaderboardViewProps) {
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);

  const load = useCallback(async () => {
    const list = await fetchLeaderboard();
    setEntries(list);
  }, []);

  useEffect(() => {
    load();
    const interval = setInterval(load, 2000);
    return () => clearInterval(interval);
  }, [load]);

  // Refetch when a run is saved (from Live tab) or when user switches back to this tab
  useEffect(() => {
    const onSaved = (e: Event) => {
      const detail = (e as CustomEvent<LeaderboardEntry[] | undefined>).detail;
      if (Array.isArray(detail) && detail.length > 0) setEntries(detail);
      else load();
    };
    const onVisibility = () => { if (typeof document !== "undefined" && document.visibilityState === "visible") load(); };
    window.addEventListener(LEADERBOARD_SAVED_EVENT, onSaved);
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      window.removeEventListener(LEADERBOARD_SAVED_EVENT, onSaved);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [load]);

  return (
    <View style={styles.container}>
      {/* Background Number Watermark */}
      <View style={styles.watermarkContainer}>
        <Text style={styles.watermarkNumber}>{backgroundNumber}</Text>
      </View>

      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>UTRA MATCH</Text>
        <Text style={styles.headerSubtitle}>Leaderboard</Text>
      </View>

      {/* Main Content */}
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        {/* High Score Banner */}
        {entries.length > 0 && (
          <View style={styles.highScoreBanner}>
            <Text style={styles.highScoreStar}>★</Text>
            <View style={styles.highScoreContent}>
              <Text style={styles.highScoreLabel}>HIGH SCORE</Text>
              <View style={styles.highScoreTeamRow}>
                <View style={styles.highScoreTeamBox}>
                  <Text style={styles.highScoreTeamNumber}>{entries[0].team}</Text>
                </View>
                <Text style={styles.highScoreValue}>{entries[0].score}</Text>
              </View>
            </View>
            <Text style={styles.highScoreStar}>★</Text>
          </View>
        )}

        {/* Leaderboard Table */}
        <View style={styles.tableContainer}>
          {/* Table Header: Team = team number only (no separate # column) */}
          <View style={styles.tableHeaderRow}>
            <Text style={[styles.tableHeaderCell, styles.cellTeam]}>TEAM</Text>
            <Text style={[styles.tableHeaderCell, styles.cellScore]}>SCORE</Text>
            <Text style={[styles.tableHeaderCell, styles.cellTime]}>TIME</Text>
            <Text style={[styles.tableHeaderCell, styles.cellObstacle]}>OBS</Text>
            <Text style={[styles.tableHeaderCell, styles.cellBonus]}>60s</Text>
            <Text style={[styles.tableHeaderCell, styles.cellBox]}>BOX</Text>
          </View>

          {/* Table Rows: placeholder with 0/— when empty, else real entries */}
          {(entries.length === 0 ? [{
            rank: 0,
            team: "—",
            score: 0,
            time: "0:00",
            obstacleTouches: 0,
            completedUnder60: false,
            boxDrop: "none" as const,
          }] : entries).map((entry, index) => (
            <View
              key={entries.length === 0 ? "placeholder" : `${entry.team}-${index}`}
              style={[
                styles.tableRow,
                index % 2 === 0 ? styles.tableRowLight : styles.tableRowDark,
              ]}
            >
              <View style={[styles.cellTeam]}>
                <View style={styles.teamBadge}>
                  <Text style={styles.teamBadgeText}>{entry.team}</Text>
                </View>
              </View>
              <Text style={[styles.tableCell, styles.cellScore, styles.scoreText]}>
                {entry.score}
              </Text>
              <Text style={[styles.tableCell, styles.cellTime]}>{entry.time}</Text>
              <Text style={[styles.tableCell, styles.cellObstacle]}>{entry.obstacleTouches}</Text>
              <Text style={[styles.tableCell, styles.cellBonus]}>
                {entry.completedUnder60 ? "✓" : "-"}
              </Text>
              <Text style={[styles.tableCell, styles.cellBox]}>
                {entry.boxDrop === "none" ? "-" : entry.boxDrop.charAt(0).toUpperCase()}
              </Text>
            </View>
          ))}
        </View>
      </ScrollView>

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
    fontSize: Math.min(SCREEN_WIDTH * 0.8, 500),
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
  scrollView: {
    flex: 1,
    zIndex: 1,
  },
  scrollContent: {
    padding: 20,
  },
  highScoreBanner: {
    backgroundColor: COLORS.yellow,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 4,
    marginBottom: 20,
  },
  highScoreStar: {
    fontSize: 32,
    color: COLORS.darkText,
  },
  highScoreContent: {
    alignItems: "center",
    marginHorizontal: 20,
  },
  highScoreLabel: {
    color: COLORS.darkText,
    fontSize: 18,
    fontWeight: "bold",
    marginBottom: 8,
  },
  highScoreTeamRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 16,
  },
  highScoreTeamBox: {
    backgroundColor: "#EF4444",
    paddingVertical: 6,
    paddingHorizontal: 16,
    borderRadius: 4,
  },
  highScoreTeamNumber: {
    color: COLORS.white,
    fontSize: 20,
    fontWeight: "bold",
  },
  highScoreValue: {
    color: COLORS.darkText,
    fontSize: 36,
    fontWeight: "900",
  },
  tableContainer: {
    backgroundColor: COLORS.white,
    borderRadius: 4,
    overflow: "hidden",
  },
  tableHeaderRow: {
    backgroundColor: COLORS.headerDark,
    flexDirection: "row",
    paddingVertical: 12,
    paddingHorizontal: 16,
  },
  tableHeaderCell: {
    color: COLORS.white,
    fontSize: 12,
    fontWeight: "bold",
    textAlign: "center",
  },
  tableRow: {
    flexDirection: "row",
    paddingVertical: 14,
    paddingHorizontal: 16,
    alignItems: "center",
  },
  tableRowLight: {
    backgroundColor: COLORS.tableRowLight,
  },
  tableRowDark: {
    backgroundColor: COLORS.tableRowDark,
  },
  tableCell: {
    color: COLORS.darkText,
    fontSize: 14,
    textAlign: "center",
  },
  cellTeam: {
    width: 80,
    alignItems: "center",
  },
  cellScore: {
    width: 70,
  },
  cellTime: {
    width: 60,
  },
  cellObstacle: {
    width: 50,
  },
  cellBonus: {
    width: 50,
  },
  cellBox: {
    width: 50,
  },
  scoreText: {
    fontSize: 20,
    fontWeight: "900",
    color: COLORS.primaryBlue,
  },
  teamBadge: {
    backgroundColor: COLORS.primaryBlue,
    paddingVertical: 4,
    paddingHorizontal: 12,
    borderRadius: 4,
  },
  teamBadgeText: {
    color: COLORS.white,
    fontSize: 14,
    fontWeight: "bold",
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
