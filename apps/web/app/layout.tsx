import "./globals.css";
import type { Metadata } from "next";
import AppNav from "../components/AppNav";
export const metadata: Metadata = { title: {default: "instaHub — AI Creator Studio", template: "%s · instaHub"}, description: "Create, refine, schedule and publish AI-powered social content." };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="en"><body><AppNav/>{children}</body></html>; }
