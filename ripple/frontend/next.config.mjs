/** @type {import('next').NextConfig} */
export default {
  reactStrictMode: true,
  output: process.env.STANDALONE ? "standalone" : undefined,   // Docker sets STANDALONE=1
};
