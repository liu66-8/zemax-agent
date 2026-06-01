import type { Metadata } from "next";
import { ModalProvider } from "./components/Modal";
import "./globals.css";

export const metadata: Metadata = {
  title: "Zemax Agent — 光学工程工作台",
  description: "AI 驱动光学设计工作平台",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;450;500;600;700&display=swap" rel="stylesheet" />
      </head>
      <body>
        <ModalProvider>{children}</ModalProvider>
      </body>
    </html>
  );
}
