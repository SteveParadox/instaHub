import "./globals.css";
import type { Metadata } from "next";
import AppNav from "../components/AppNav";
export const metadata: Metadata = { title: "instaHub", description: "AI Creator Studio for Instagram" };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="en"><body><AppNav/>{children}</body></html>; }
