"use client";

import { useState } from "react";
import { View, StyleSheet, SafeAreaView, TextInput, Text, TouchableOpacity } from "react-native";
import { NavigationTabs } from "@/components/rn/navigation-tabs";
import { LiveMatchView } from "@/components/rn/live-match-view";
import { ScoreBreakdownView } from "@/components/rn/score-breakdown-view";
import { LeaderboardView } from "@/components/rn/leaderboard-view";
import { COLORS } from "@/lib/types";

export default function HomePage() {
  const [activeTab, setActiveTab] = useState<"live" | "breakdown" | "leaderboard">("live");
  const [backgroundNumber, setBackgroundNumber] = useState("8");
  const [showSettings, setShowSettings] = useState(false);
  const [tempNumber, setTempNumber] = useState("8");

  const handleSaveNumber = () => {
    setBackgroundNumber(tempNumber);
    setShowSettings(false);
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.container}>
        {/* Settings Button */}
        <TouchableOpacity 
          style={styles.settingsButton}
          onPress={() => {
            setTempNumber(backgroundNumber);
            setShowSettings(!showSettings);
          }}
        >
          <Text style={styles.settingsButtonText}>⚙</Text>
        </TouchableOpacity>

        {/* Settings Panel */}
        {showSettings && (
          <View style={styles.settingsPanel}>
            <Text style={styles.settingsLabel}>Background Number:</Text>
            <View style={styles.settingsRow}>
              <TextInput
                style={styles.settingsInput}
                value={tempNumber}
                onChangeText={setTempNumber}
                keyboardType="default"
                maxLength={3}
              />
              <TouchableOpacity style={styles.saveButton} onPress={handleSaveNumber}>
                <Text style={styles.saveButtonText}>SAVE</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {/* Navigation */}
        <NavigationTabs activeTab={activeTab} onTabChange={setActiveTab} />

        {/* Content */}
        <View style={styles.content}>
          {activeTab === "live" && (
            <LiveMatchView
              backgroundNumber={backgroundNumber}
              onTeamSet={(team) => setBackgroundNumber(team)}
            />
          )}
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
  },
  container: {
    flex: 1,
    backgroundColor: COLORS.primaryBlue,
    position: "relative",
  },
  content: {
    flex: 1,
  },
  settingsButton: {
    position: "absolute",
    top: 10,
    right: 10,
    zIndex: 100,
    backgroundColor: COLORS.darkBlue,
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 2,
    borderColor: COLORS.white,
  },
  settingsButtonText: {
    color: COLORS.white,
    fontSize: 20,
  },
  settingsPanel: {
    position: "absolute",
    top: 60,
    right: 10,
    zIndex: 100,
    backgroundColor: COLORS.headerDark,
    padding: 16,
    borderRadius: 8,
    borderWidth: 2,
    borderColor: COLORS.white,
    minWidth: 200,
  },
  settingsLabel: {
    color: COLORS.white,
    fontSize: 14,
    fontWeight: "600",
    marginBottom: 8,
  },
  settingsRow: {
    flexDirection: "row",
    gap: 8,
  },
  settingsInput: {
    flex: 1,
    backgroundColor: COLORS.white,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 4,
    fontSize: 18,
    fontWeight: "bold",
    textAlign: "center",
    color: COLORS.darkText,
  },
  saveButton: {
    backgroundColor: COLORS.yellow,
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 4,
    justifyContent: "center",
  },
  saveButtonText: {
    color: COLORS.darkText,
    fontSize: 14,
    fontWeight: "bold",
  },
});
