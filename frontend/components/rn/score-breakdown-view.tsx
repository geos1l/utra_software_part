"use client";

import { useState, useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  Dimensions,
} from "react-native";
import { COLORS, type MatchState } from "@/lib/types";
import { fetchState } from "@/lib/api";

const { width: SCREEN_WIDTH } = Dimensions.get("window");

interface ScoreBreakdownViewProps {
  backgroundNumber?: string;
}

export function ScoreBreakdownView({ backgroundNumber = "8" }: ScoreBreakdownViewProps) {
  const [state, setState] = useState<MatchState>({
    teamNumber: "3083",
    score: 51,
    timerSeconds: 0,
    isRunning: false,
    obstacleTouches: 9,
    completedUnder60: true,
    boxDrop: "none",
  });

  useEffect(() => {
    const poll = async () => {
      const next = await fetchState();
      if (next) setState(next);
    };
    const interval = setInterval(poll, 500);
    poll();
    return () => clearInterval(interval);
  }, []);

  // Use backend score breakdown when available (5-touches, under60=5, box_drop=5/4/1)
  const bd = state.scoreBreakdown;
  const obstaclePoints = bd?.obstacles ?? 0;
  const under60Points = bd?.completedUnder60 ?? (state.completedUnder60 ? 5 : 0);
  const boxDropPoints = bd?.boxDrop ?? 0;
  const totalScore = state.score;

  return (
    <View style={styles.container}>
      {/* Background Number Watermark */}
      <View style={styles.watermarkContainer}>
        <Text style={styles.watermarkNumber}>{backgroundNumber}</Text>
      </View>

      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>UTRA MATCH</Text>
        <Text style={styles.headerSubtitle}>Score Breakdown</Text>
      </View>

      {/* Main Content */}
      <View style={styles.mainContent}>
        {/* Team Info Panel - same team number as live page (backgroundNumber) */}
        <View style={styles.teamPanel}>
          <View style={styles.teamBox}>
            <Text style={styles.teamNumber}>{backgroundNumber || "—"}</Text>
          </View>
          <Text style={styles.scoreLabel}>TOTAL SCORE</Text>
          <Text style={styles.score}>{totalScore}</Text>
        </View>

        {/* Score Breakdown Table */}
        <View style={styles.tableContainer}>
          {/* Table Header */}
          <View style={styles.tableHeaderRow}>
            <Text style={styles.tableHeaderCell}>CATEGORY</Text>
            <Text style={styles.tableHeaderCellRight}>POINTS</Text>
          </View>

          {/* Obstacles (5 − touches) */}
          <View style={[styles.tableRow, styles.tableRowLight]}>
            <Text style={styles.tableCellLabel}>OBSTACLES</Text>
            <Text style={styles.tableCellValue}>{obstaclePoints}</Text>
          </View>

          {/* Completed Under 60s (+5) */}
          <View style={[styles.tableRow, styles.tableRowDark]}>
            <Text style={styles.tableCellLabel}>UNDER 60s BONUS</Text>
            <Text style={styles.tableCellValue}>{under60Points}</Text>
          </View>

          {/* Box Drop (5/4/1) */}
          <View style={[styles.tableRow, styles.tableRowLight]}>
            <Text style={styles.tableCellLabel}>BOX DROP ({state.boxDrop === "fullyIn" ? "FULLY IN" : state.boxDrop === "partial" ? "PARTIAL" : state.boxDrop === "mostlyOut" ? "MOSTLY OUT" : "NONE"})</Text>
            <Text style={styles.tableCellValue}>{boxDropPoints}</Text>
          </View>

          {/* Total */}
          <View style={[styles.tableRow, styles.totalRow]}>
            <Text style={styles.totalLabel}>TOTAL</Text>
            <Text style={styles.totalValue}>{totalScore}</Text>
          </View>
        </View>
      </View>

      {/* Advances To Section */}
      <View style={styles.advancesContainer}>
        <View style={styles.advancesBox}>
          <Text style={styles.advancesTitle}>Advances to:</Text>
          <Text style={styles.advancesText}>Round 2 - Match 5</Text>
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
  mainContent: {
    flexDirection: "row",
    flex: 1,
    padding: 20,
    zIndex: 1,
  },
  teamPanel: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    paddingRight: 40,
  },
  teamBox: {
    backgroundColor: COLORS.teamBoxBlue,
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 4,
    marginBottom: 30,
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
    fontSize: 14,
    fontWeight: "600",
    marginBottom: 8,
    opacity: 0.8,
  },
  score: {
    color: COLORS.white,
    fontSize: 100,
    fontWeight: "900",
    lineHeight: 100,
  },
  tableContainer: {
    flex: 1.5,
    backgroundColor: COLORS.white,
    borderRadius: 4,
    overflow: "hidden",
    alignSelf: "center",
  },
  tableHeaderRow: {
    backgroundColor: COLORS.headerDark,
    flexDirection: "row",
    paddingVertical: 14,
    paddingHorizontal: 20,
  },
  tableHeaderCell: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: "bold",
    flex: 1,
  },
  tableHeaderCellRight: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: "bold",
    textAlign: "right",
    minWidth: 80,
  },
  tableRow: {
    flexDirection: "row",
    paddingVertical: 16,
    paddingHorizontal: 20,
    alignItems: "center",
  },
  tableRowLight: {
    backgroundColor: COLORS.tableRowLight,
  },
  tableRowDark: {
    backgroundColor: COLORS.tableRowDark,
  },
  tableCellLabel: {
    color: COLORS.darkText,
    fontSize: 18,
    fontWeight: "600",
    flex: 1,
  },
  tableCellValue: {
    color: COLORS.darkText,
    fontSize: 24,
    fontWeight: "bold",
    textAlign: "right",
    minWidth: 80,
  },
  totalRow: {
    backgroundColor: COLORS.yellow,
    paddingVertical: 18,
  },
  totalLabel: {
    color: COLORS.darkText,
    fontSize: 20,
    fontWeight: "bold",
    flex: 1,
  },
  totalValue: {
    color: COLORS.darkText,
    fontSize: 28,
    fontWeight: "900",
    textAlign: "right",
    minWidth: 80,
  },
  advancesContainer: {
    paddingHorizontal: 20,
    paddingBottom: 20,
    zIndex: 1,
  },
  advancesBox: {
    backgroundColor: COLORS.primaryBlue,
    borderWidth: 2,
    borderColor: COLORS.white,
    borderRadius: 4,
    paddingVertical: 12,
    paddingHorizontal: 20,
    alignSelf: "flex-start",
  },
  advancesTitle: {
    color: COLORS.white,
    fontSize: 14,
    fontWeight: "600",
    marginBottom: 4,
  },
  advancesText: {
    color: COLORS.white,
    fontSize: 16,
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
