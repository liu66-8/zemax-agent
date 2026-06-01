/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",
  distDir: "out",
  images: { unoptimized: true },
  transpilePackages: ["lucide-react"],
};

export default nextConfig;
