"use client";

import { useState } from "react";
import { View, StyleSheet, SafeAreaView, Platform } from "react-native";
import { NavigationTabs } from "./navigation-tabs";
import { LiveMatchView } from "./live-match-view";
import { ScoreBreakdownView } from "./score-breakdown-view";
import { LeaderboardView } from "./leaderboard-view";
import { COLORS } from "@/lib/types";

interface MatchOverlayAppProps {
  backgroundNumber?: string;
}

export function MatchOverlayApp({ backgroundNumber = "8" }: MatchOverlayAppProps) {
  const [activeTab, setActiveTab] = useState<"live" | "breakdown" | "leaderboard">("live");

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.container}>
        {/* Navigation */}
        <NavigationTabs activeTab={activeTab} onTabChange={setActiveTab} />

        {/* Content */}
        <View style={styles.content}>
          {activeTab === "live" && <LiveMatchView backgroundNumber={backgroundNumber} />}
          {activeTab === "breakdown" && <ScoreBreakdownView backgroundNumber={backgroundNumber} />}
          {activeTab === "leaderboard" && <LeaderboardView backgroundNumber={backgroundNumber} />}
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: COLORS.headerDark,
    // Handle notch on iOS
    ...(Platform.OS === "ios"
      ? {}
      : {
          paddingTop: 0,
        }),
  },
  container: {
    flex: 1,
    backgroundColor: COLORS.primaryBlue,
  },
  content: {
    flex: 1,
  },
});
