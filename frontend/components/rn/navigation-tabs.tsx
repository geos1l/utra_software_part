"use client";

import { View, Text, TouchableOpacity, StyleSheet } from "react-native";
import { COLORS } from "@/lib/types";

interface NavigationTabsProps {
  activeTab: "live" | "breakdown" | "leaderboard";
  onTabChange: (tab: "live" | "breakdown" | "leaderboard") => void;
}

export function NavigationTabs({ activeTab, onTabChange }: NavigationTabsProps) {
  const tabs = [
    { id: "live" as const, label: "LIVE" },
    { id: "breakdown" as const, label: "BREAKDOWN" },
    { id: "leaderboard" as const, label: "LEADERBOARD" },
  ];

  return (
    <View style={styles.container}>
      {tabs.map((tab) => (
        <TouchableOpacity
          key={tab.id}
          style={[styles.tab, activeTab === tab.id && styles.activeTab]}
          onPress={() => onTabChange(tab.id)}
        >
          <Text style={[styles.tabText, activeTab === tab.id && styles.activeTabText]}>
            {tab.label}
          </Text>
        </TouchableOpacity>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    backgroundColor: COLORS.darkBlue,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  tab: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 16,
    alignItems: "center",
    borderRadius: 4,
    marginHorizontal: 4,
  },
  activeTab: {
    backgroundColor: COLORS.yellow,
  },
  tabText: {
    color: COLORS.white,
    fontSize: 14,
    fontWeight: "bold",
  },
  activeTabText: {
    color: COLORS.darkText,
  },
});
