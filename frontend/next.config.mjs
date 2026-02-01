import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  // Alias react-native to react-native-web so RN components run in the browser (RN's index uses Flow syntax webpack can't parse)
  webpack: (config) => {
    const rnwPath = path.resolve(__dirname, "node_modules", "react-native-web");
    config.resolve.alias = {
      ...config.resolve.alias,
      "react-native": rnwPath,
      "react-native-web": rnwPath,
    };
    return config;
  },
  // Use frontend as workspace root (avoids Next.js picking parent due to lockfiles)
  turbopack: { root: __dirname },
};

export default nextConfig;
