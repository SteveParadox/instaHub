import type {ReactNode, SVGProps} from "react";

export type IconName = "sparkles"|"sliders"|"text"|"send"|"calendar"|"palette"|"plug"|"instagram"|"pinterest"|"video"|"chevrons"|"logout"|"login"|"menu"|"close"|"image"|"upload"|"wand"|"copy"|"check"|"clock"|"arrow"|"plus"|"refresh"|"crop"|"expand"|"layers"|"trash"|"external"|"shield";

const paths: Record<IconName, ReactNode> = {
  sparkles: <><path d="m12 3-1.2 3.8L7 8l3.8 1.2L12 13l1.2-3.8L17 8l-3.8-1.2L12 3Z"/><path d="m5 14-.7 2.3L2 17l2.3.7L5 20l.7-2.3L8 17l-2.3-.7L5 14Zm13-1-.8 2.2L15 16l2.2.8L18 19l.8-2.2L21 16l-2.2-.8L18 13Z"/></>,
  sliders: <><path d="M4 7h7m4 0h5M4 17h3m4 0h9"/><circle cx="13" cy="7" r="2"/><circle cx="9" cy="17" r="2"/></>,
  text: <><path d="M5 6h14M9 6v12m6-12v12M7 18h4m2 0h4"/></>,
  send: <path d="m21 3-7.4 18-4.2-7.4L2 9.4 21 3Zm-11.6 10.6L14 9"/>,
  calendar: <><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 10h18"/></>,
  palette: <><path d="M12 3a9 9 0 0 0 0 18h1.5a1.5 1.5 0 0 0 0-3H12a2 2 0 0 1 0-4h3.5A5.5 5.5 0 0 0 21 8.5C21 5.5 16.9 3 12 3Z"/><circle cx="7.5" cy="10" r=".8"/><circle cx="10" cy="6.5" r=".8"/><circle cx="15" cy="7" r=".8"/></>,
  plug: <><path d="M8 12h8m-6-8v5m4-5v5M7 9h10v3a5 5 0 0 1-5 5v4"/></>,
  instagram: <><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r=".8" fill="currentColor"/></>,
  pinterest: <><circle cx="12" cy="12" r="9"/><path d="M9.5 19 12 9.5m-2.8 4.2c-1.7-2.7-.4-6.5 3.2-6.5 2.8 0 4.4 2 3.8 4.5-.5 2.2-1.8 3.8-3.5 3.4-1.3-.3-1.8-1.5-1.3-3.1"/></>,
  video: <><rect x="3" y="5" width="14" height="14" rx="2"/><path d="m17 10 4-2v8l-4-2v-4Z"/></>,
  chevrons: <path d="m8 9 4-4 4 4m0 6-4 4-4-4"/>, logout: <><path d="M10 5H5v14h5m5-3 4-4-4-4m4 4H9"/></>, login: <><path d="M14 5h5v14h-5m-5-3-4-4 4-4m-4 4h10"/></>, menu: <path d="M4 7h16M4 12h16M4 17h16"/>, close: <path d="m6 6 12 12M18 6 6 18"/>,
  image: <><rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="8.5" cy="9" r="1.5"/><path d="m4 17 4.5-4 3.5 3 2.5-2 5.5 5"/></>, upload: <><path d="M12 16V4m-4 4 4-4 4 4M4 15v5h16v-5"/></>, wand: <><path d="m4 20 11-11m-8-2 2 2m6-6 2 2m1 6 3 1-3 1-1 3-1-3-3-1 3-1 1-3 1 3Z"/></>, copy: <><rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"/></>, check: <path d="m5 12 4 4L19 6"/>, clock: <><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></>, arrow: <path d="M5 12h14m-5-5 5 5-5 5"/>, plus: <path d="M12 5v14M5 12h14"/>, refresh: <><path d="M20 7v5h-5M4 17v-5h5"/><path d="M18 9a7 7 0 0 0-12-2M6 15a7 7 0 0 0 12 2"/></>, crop: <path d="M7 3v14a2 2 0 0 0 2 2h12M3 7h14a2 2 0 0 1 2 2v12"/>, expand: <><path d="M8 3H3v5m13-5h5v5M8 21H3v-5m13 5h5v-5"/></>, layers: <><path d="m12 3 9 5-9 5-9-5 9-5Z"/><path d="m3 12 9 5 9-5M3 16l9 5 9-5"/></>, trash: <><path d="M4 7h16M9 7V4h6v3m3 0-1 14H7L6 7m4 4v6m4-6v6"/></>, external: <><path d="M14 4h6v6m0-6-9 9"/><path d="M18 13v6a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h6"/></>, shield: <><path d="M12 3 5 6v5c0 4.6 2.8 8.3 7 10 4.2-1.7 7-5.4 7-10V6l-7-3Z"/><path d="m9 12 2 2 4-5"/></>,
};

export function Icon({name, size=20, ...props}: {name: IconName; size?: number} & SVGProps<SVGSVGElement>) {
  return <svg aria-hidden="true" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" {...props}>{paths[name]}</svg>;
}

export function PageHeader({eyebrow, title, accent, description, actions}: {eyebrow:string; title:string; accent?:string; description?:string; actions?:ReactNode}) {
  return <header className="page-header"><div><p className="eyebrow">{eyebrow}</p><h1>{title}{accent && <> <em>{accent}</em></>}</h1>{description && <p className="page-description">{description}</p>}</div>{actions && <div className="page-actions">{actions}</div>}</header>;
}

export function EmptyState({icon="image", title, description, action}: {icon?:IconName; title:string; description:string; action?:ReactNode}) {
  return <div className="empty-state"><span className="empty-icon"><Icon name={icon}/></span><h3>{title}</h3><p>{description}</p>{action}</div>;
}

export function StatusBadge({status}: {status:string}) {
  const key = status.toLowerCase();
  const tone = ["completed","published","connected","active","ready"].some(x=>key.includes(x)) ? "success" : ["failed","error","cancelled"].some(x=>key.includes(x)) ? "danger" : ["queued","generating","publishing","retrying","scheduled","processing"].some(x=>key.includes(x)) ? "pending" : "neutral";
  return <span className={`status-badge ${tone}`}><span/>{status}</span>;
}

export function InlineNotice({children, tone="info"}: {children:ReactNode; tone?:"info"|"success"|"error"}) {
  return <div className={`inline-notice ${tone}`} role={tone === "error" ? "alert" : "status"}>{children}</div>;
}

export function LoadingDots(){return <span className="loading-dots" aria-hidden="true"><i/><i/><i/></span>}
