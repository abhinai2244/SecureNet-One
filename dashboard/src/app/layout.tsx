import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SecureNet One — Zero Trust Security Platform",
  description: "Enterprise-grade Zero Trust security platform with WireGuard tunneling, DNS-over-HTTPS, device posture monitoring, and centralized policy management.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
