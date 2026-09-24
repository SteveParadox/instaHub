"use client";

import Link from "next/link";
import {usePathname, useRouter} from "next/navigation";

const links = [
  ["/", "Create"], ["/editor", "Edit"], ["/captions", "Captions"],
  ["/publish", "Publish"], ["/schedule", "Calendar"], ["/brand-studio", "Brand"],
  ["/providers", "Connectors"], ["/instagram", "Instagram"], ["/pinterest", "Pinterest"],
  ["/video-studio", "Video"],
];

export default function AppNav(){
  const path=usePathname(),router=useRouter();
  function signOut(){localStorage.removeItem("instahub_access_token");localStorage.removeItem("instahub_workspace_id");router.push("/auth")}
  return <nav className="app-nav"><Link className="brand" href="/">insta<span>Hub</span></Link><div className="nav-links">{links.map(([href,label])=><Link className={path===href?"current":""} href={href} key={href}>{label}</Link>)}</div><div className="nav-actions"><Link href="/auth">Account</Link><button onClick={signOut}>Sign out</button></div></nav>
}
