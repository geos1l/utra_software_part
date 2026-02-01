export interface ScoreBreakdown {
  obstacles: number;
  completedUnder60: number;
  boxDrop: number;
}

export interface MatchState {
  teamNumber: string;
  score: number;
  timerSeconds: number;
  isRunning: boolean;
  obstacleTouches: number;
  completedUnder60: boolean;
  boxDrop: "none" | "fullyIn" | "partial" | "mostlyOut";
  /** Points from backend (obstacles = 5-touches, under60 = 5, box_drop = 5/4/1) */
  scoreBreakdown?: ScoreBreakdown;
}

export interface LeaderboardEntry {
  rank: number;
  team: string;
  score: number;
  time: string;
  obstacleTouches: number;
  completedUnder60: boolean;
  boxDrop: "none" | "fullyIn" | "partial" | "mostlyOut";
}

export const COLORS = {
  // From FRC screenshot - blue alliance side
  primaryBlue: "#0066B3", // Main blue from alliance box
  darkBlue: "#003366", // Darker blue for backgrounds
  navyBackground: "#1A2744", // Dark navy background
  
  // Accent colors
  yellow: "#FFD700", // Yellow highlight/winner
  
  // Table colors from screenshot
  tableRowLight: "#FFFFFF", // White rows
  tableRowDark: "#E8E8E8", // Light gray alternating rows
  
  // Text colors
  white: "#FFFFFF",
  black: "#000000",
  darkText: "#1A1A1A",
  
  // Header/footer
  headerDark: "#1A1A2E", // Very dark blue/black header
  
  // Team number boxes
  teamBoxBlue: "#0066B3",
  
  // Watermark number
  watermarkBlue: "#004D99", // Slightly darker for the background number
} as const;
