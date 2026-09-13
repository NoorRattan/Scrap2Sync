import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import "@fontsource-variable/manrope";
import "@fontsource/instrument-serif/latin-400-italic.css";
import "./globals.css";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Scrap2Sync — Your notes, ready for standup",
  description:
    "Organize rough developer notes into an editable standup draft. Review, adjust, and copy your update.",
  robots: { index: true, follow: true },
  openGraph: {
    title: "Scrap2Sync — Less noise. More signal.",
    description:
      "Turn rough notes into a clear, editable standup. Your thoughts, beautifully together.",
    type: "website",
    locale: "en_US",
  },
  twitter: {
    card: "summary",
    title: "Scrap2Sync — Less noise. More signal.",
    description:
      "A little clarity before your daily sync. Capture, organize, review, and copy.",
  },
};

export const viewport: Viewport = {
  themeColor: "#141816",
  colorScheme: "dark",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <a className="skip-link" href="#main-content">
          Skip to main content
        </a>
        {children}
      </body>
    </html>
  );
}
