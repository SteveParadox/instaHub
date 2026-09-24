"use client";

import {FormEvent,useState} from "react";
import {useRouter} from "next/navigation";

const api=process.env.NEXT_PUBLIC_API_URL??"http://localhost:8000";
const supabase=process.env.NEXT_PUBLIC_SUPABASE_URL??"";
const anon=process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY??"";

export default function Auth(){
  const router=useRouter();
  const[mode,setMode]=useState<"login"|"signup">("login"),[email,setEmail]=useState(""),[password,setPassword]=useState(""),[workspaceName,setWorkspaceName]=useState("My studio"),[message,setMessage]=useState(""),[busy,setBusy]=useState(false);
  async function submit(event:FormEvent){event.preventDefault();setBusy(true);setMessage("");
    if(!supabase||!anon){setMessage("Supabase public configuration is missing.");setBusy(false);return}
    const path=mode==="login"?"/auth/v1/token?grant_type=password":"/auth/v1/signup";
    const authResponse=await fetch(supabase+path,{method:"POST",headers:{"Content-Type":"application/json",apikey:anon},body:JSON.stringify({email,password})});
    const authData=await authResponse.json();
    if(!authResponse.ok){setMessage(authData.msg??authData.error_description??"Authentication failed.");setBusy(false);return}
    if(!authData.access_token){setMessage("Check your email to confirm your account, then sign in.");setBusy(false);return}
    localStorage.setItem("instahub_access_token",authData.access_token);
    const headers={Authorization:"Bearer "+authData.access_token,"Content-Type":"application/json"};
    await fetch(api+"/v1/me",{headers});
    const workspacesResponse=await fetch(api+"/v1/workspaces",{headers});let workspaces=workspacesResponse.ok?await workspacesResponse.json():[];
    if(!workspaces.length){const created=await fetch(api+"/v1/workspaces",{method:"POST",headers,body:JSON.stringify({name:workspaceName})});if(!created.ok){setMessage("Signed in, but the workspace could not be created.");setBusy(false);return}workspaces=[await created.json()]}
    localStorage.setItem("instahub_workspace_id",workspaces[0].id);router.push("/");router.refresh();
  }
  return <main className="auth-page"><section className="auth-copy"><p className="kicker">AI CREATOR OPERATING SYSTEM</p><h1>From idea<br/>to <i>everywhere.</i></h1><p>Generate, refine, caption, schedule and publish a consistent visual world from one studio.</p><div className="mini-grid"><span>IMAGE</span><span>CAPTION</span><span>SCHEDULE</span><span>PUBLISH</span></div></section><section className="auth-card"><div className="tabs"><button className={mode==="login"?"active":""} onClick={()=>setMode("login")}>Sign in</button><button className={mode==="signup"?"active":""} onClick={()=>setMode("signup")}>Create account</button></div><form onSubmit={submit}><label>Email<input type="email" value={email} onChange={e=>setEmail(e.target.value)} required placeholder="you@studio.com"/></label><label>Password<input type="password" minLength={8} value={password} onChange={e=>setPassword(e.target.value)} required/></label>{mode==="signup"&&<label>Workspace name<input value={workspaceName} onChange={e=>setWorkspaceName(e.target.value)} minLength={2} required/></label>}<button className="primary" disabled={busy}>{busy?"Preparing your studio…":mode==="login"?"Enter studio":"Create my studio"}</button>{message&&<p className="form-message">{message}</p>}</form><small>Credentials are handled by Supabase. Provider and social tokens stay encrypted on the API.</small></section></main>
}
