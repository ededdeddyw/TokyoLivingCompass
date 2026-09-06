import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // 駅ページは全て静的生成する（SEO が生命線のため）
  output: "standalone",
};

export default nextConfig;
