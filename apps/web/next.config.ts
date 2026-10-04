import type { NextConfig } from "next";
import { fileURLToPath } from "node:url";

const config: NextConfig = {
  reactStrictMode: true,
  devIndicators: false,
  output: "standalone",
  outputFileTracingRoot: fileURLToPath(new URL("../..", import.meta.url)),
};
export default config;
