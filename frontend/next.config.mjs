/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Disable static generation for pages using client-side state
  experimental: {
    missingSuspenseWithCSRBailout: false,
  },
}

export default nextConfig