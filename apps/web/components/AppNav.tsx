"use client";

import Link from "next/link";
import {useEffect, useState} from "react";
import {usePathname, useRouter} from "next/navigation";
import {Icon} from "./StudioUI";

const primary = [
  {href: "/", label: "Create", icon: "sparkles"},
  {href: "/editor", label: "Edit", icon: "sliders"},
  {href: "/captions", label: "Captions", icon: "text"},
  {href: "/publish", label: "Publish", icon: "send"},
  {href: "/schedule", label: "Calendar", icon: "calendar"},
] as const;

const manage = [
  {href: "/brand-studio", label: "Brand studio", icon: "palette"},
  {href: "/providers", label: "AI connectors", icon: "plug"},
  {href: "/instagram", label: "Instagram", icon: "instagram"},
  {href: "/pinterest", label: "Pinterest", icon: "pinterest"},
  {href: "/video-studio", label: "Video studio", icon: "video"},
] as const;

const routeLabels = [...primary, ...manage];

export default function AppNav() {
  const path = usePathname();
  const router = useRouter();
  const [menuOpen, setMenuOpen] = useState(false);
  const [signedIn, setSignedIn] = useState(false);

  useEffect(() => {
    setSignedIn(Boolean(localStorage.getItem("instahub_access_token")));
    setMenuOpen(false);
  }, [path]);

  function signOut() {
    localStorage.removeItem("instahub_access_token");
    localStorage.removeItem("instahub_workspace_id");
    setSignedIn(false);
    router.push("/auth");
  }

  function NavLink({href, label, icon}: (typeof routeLabels)[number]) {
    const active = path === href;
    return (
      <Link href={href} className={active ? "nav-link current" : "nav-link"} aria-current={active ? "page" : undefined}>
        <Icon name={icon} size={18}/><span>{label}</span>
      </Link>
    );
  }

  const title = routeLabels.find((item) => item.href === path)?.label ?? "Account";

  if (path === "/auth") return <Link className="auth-logo brand" href="/" aria-label="instaHub home"><span className="brand-mark"><Icon name="sparkles" size={17}/></span>insta<span>Hub</span></Link>;

  return <>
    <aside className="app-sidebar" aria-label="Main navigation">
      <Link className="brand" href="/" aria-label="instaHub home"><span className="brand-mark"><Icon name="sparkles" size={17}/></span>insta<span>Hub</span></Link>
      <div className="workspace-chip"><span className="workspace-avatar">IH</span><span><small>Current workspace</small><b>Creator studio</b></span><Icon name="chevrons" size={14}/></div>
      <nav className="sidebar-nav">
        <p className="nav-label">Create</p>
        {primary.map((item) => <NavLink {...item} key={item.href}/>)}
        <p className="nav-label">Workspace</p>
        {manage.map((item) => <NavLink {...item} key={item.href}/>)}
      </nav>
      <div className="sidebar-foot">
        <div className={signedIn ? "session-dot online" : "session-dot"}/>
        <div><b>{signedIn ? "Workspace synced" : "Guest session"}</b><small>{signedIn ? "Changes save automatically" : "Sign in to start creating"}</small></div>
        {signedIn ? <button className="icon-button" onClick={signOut} title="Sign out" aria-label="Sign out"><Icon name="logout" size={17}/></button> : <Link className="icon-button" href="/auth" title="Sign in" aria-label="Sign in"><Icon name="login" size={17}/></Link>}
      </div>
    </aside>

    <header className="mobile-topbar">
      <Link className="brand" href="/"><span className="brand-mark"><Icon name="sparkles" size={15}/></span>insta<span>Hub</span></Link>
      <span className="mobile-route">{title}</span>
      <button className="icon-button" onClick={() => setMenuOpen(true)} aria-label="Open navigation"><Icon name="menu" size={20}/></button>
    </header>

    <nav className="mobile-dock" aria-label="Primary navigation">
      {primary.map((item) => <NavLink {...item} key={item.href}/>)}
    </nav>

    {menuOpen && <div className="nav-overlay" onMouseDown={() => setMenuOpen(false)}>
      <aside className="mobile-menu" onMouseDown={(event) => event.stopPropagation()} aria-label="All navigation">
        <div className="mobile-menu-head"><div><p className="nav-label">Workspace</p><h2>Creator studio</h2></div><button className="icon-button" onClick={() => setMenuOpen(false)} aria-label="Close navigation"><Icon name="close" size={20}/></button></div>
        <nav>{[...primary, ...manage].map((item) => <NavLink {...item} key={item.href}/>)}</nav>
        <div className="mobile-menu-actions"><Link className="button secondary" href="/auth">Account</Link>{signedIn && <button className="button ghost" onClick={signOut}>Sign out</button>}</div>
      </aside>
    </div>}
  </>;
}
