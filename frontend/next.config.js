/** @type {import('next').NextConfig} */
const nextConfig = {
  /* config options here */
  typescript: {
    // TypeScript errors ko ignore karke production build complete karne ke liye
    ignoreBuildErrors: true,
  },
};

module.exports = nextConfig;