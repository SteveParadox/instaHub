"use client";

import Link from "next/link";
import {FormEvent, useEffect, useState} from "react";
import {EmptyState, Icon, InlineNotice, LoadingDots, PageHeader, StatusBadge} from "../components/StudioUI";

type Asset={id:string;delivery_url:string;width?:number;height?:number};
type Job={id:string;status:string;error_message?:string;assets:Asset[]};
type Brand={id:string;name:string};
const styles=["Photorealistic","Editorial","3D render","Anime","Minimal product"];
const ratios=["1:1","4:5","16:9"];
const ideas=["Editorial product shot","Dreamy travel scene","Bold campaign poster","Minimal studio portrait"];
const api=process.env.NEXT_PUBLIC_API_URL??"http://localhost:8000";

export default function Home(){
  const[prompt,setPrompt]=useState("");
  const[style,setStyle]=useState(styles[0]);
  const[ratio,setRatio]=useState(ratios[0]);
  const[count,setCount]=useState(1);
  const[job,setJob]=useState<Job|null>(null);
  const[history,setHistory]=useState<Asset[]>([]);
  const[error,setError]=useState("");
  const[key,setKey]=useState("");
  const[connected,setConnected]=useState<boolean|null>(null);
  const[brands,setBrands]=useState<Brand[]>([]);
  const[brand,setBrand]=useState("");
  const[loading,setLoading]=useState(true);
  const running=["queued","generating","retrying"].includes(job?.status??"");
  const auth=()=>({token:localStorage.getItem("instahub_access_token"),workspace:localStorage.getItem("instahub_workspace_id")});

  useEffect(()=>{
    const {token,workspace}=auth();
    if(!token||!workspace){setLoading(false);setConnected(false);return}
    const headers={Authorization:"Bearer "+token};
    Promise.all([
      fetch(api+"/v1/workspaces/"+workspace+"/ai-providers",{headers}).then(r=>r.ok?r.json():[]),
      fetch(api+"/v1/workspaces/"+workspace+"/assets",{headers}).then(r=>r.ok?r.json():[]),
      fetch(api+"/v1/workspaces/"+workspace+"/brands",{headers}).then(r=>r.ok?r.json():[]),
    ]).then(([providers,assets,brandRows])=>{
      setConnected(providers.find((p:{provider_name:string})=>p.provider_name==="openai")?.is_connected??false);
      setHistory(assets);setBrands(brandRows);
    }).finally(()=>setLoading(false));
  },[]);

  useEffect(()=>{
    if(!job||!["queued","generating","retrying"].includes(job.status))return;
    const t=setInterval(async()=>{const{token}=auth();const r=await fetch(api+"/v1/generation-jobs/"+job.id,{headers:{Authorization:"Bearer "+token}});if(r.ok){const n=await r.json();setJob(n);if(n.status==="completed")setHistory(a=>[...n.assets,...a])}},2000);
    return()=>clearInterval(t);
  },[job]);

  async function connect(e:FormEvent){
    e.preventDefault();setError("");const{token,workspace}=auth();
    if(!token||!workspace){setError("Sign in and select a workspace before connecting.");return}
    const r=await fetch(api+"/v1/workspaces/"+workspace+"/ai-providers/openai",{method:"PUT",headers:{"Content-Type":"application/json",Authorization:"Bearer "+token},body:JSON.stringify({api_key:key})});
    if(!r.ok){setError((await r.json()).detail??"Connection failed.");return}setKey("");setConnected(true);
  }

  async function generate(e:FormEvent){
    e.preventDefault();setError("");const{token,workspace}=auth();
    if(!token||!workspace){setError("Sign in and select a workspace before generating.");return}
    const r=await fetch(api+"/v1/generation-jobs",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+token},body:JSON.stringify({workspace_id:workspace,prompt,brand_profile_id:brand||null,style_preset:style,aspect_ratio:ratio,output_count:count})});
    if(!r.ok){setError((await r.json()).detail??"Could not start generation.");return}setJob(await r.json());
  }

  return <main><div className="page create-page">
    <PageHeader eyebrow="AI Image Studio" title="Create something" accent="worth sharing." description="Turn a rough idea into polished social content, then refine, caption, and publish it without breaking your flow." actions={<Link className="button secondary" href="/editor"><Icon name="sliders" size={16}/>Open editor</Link>}/>

    {!loading&&!connected&&<section className="connector-banner card">
      <span className="connector-icon"><Icon name="plug"/></span>
      <div><div className="connector-title"><h2>Connect OpenAI to start creating</h2><StatusBadge status="Not connected"/></div><p>Your key is encrypted and unlocks image generation, editing, captions, and hashtags.</p></div>
      <form onSubmit={connect}><label className="sr-only" htmlFor="openai-key">OpenAI API key</label><input id="openai-key" value={key} onChange={e=>setKey(e.target.value)} type="password" placeholder="OpenAI API key" required/><button className="button">Connect securely</button></form>
    </section>}

    <div className="creator-layout">
      <form className="card prompt-card" onSubmit={generate}>
        <div className="card-header"><div><p className="card-kicker">01 · Describe</p><h2>What do you want to create?</h2></div><span className="shortcut">⌘ Enter</span></div>
        <div className="card-body stack">
          <label className="field"><span className="field-label">Prompt <small className="char-count">{prompt.length} characters</small></span><textarea required value={prompt} onChange={e=>setPrompt(e.target.value)} placeholder="A luminous editorial sneaker photograph on a mirrored plinth, soft magenta rim light…"/></label>
          <div className="chip-row" aria-label="Prompt starters">{ideas.map(idea=><button type="button" className="chip" onClick={()=>setPrompt(idea+", ")} key={idea}><Icon name="plus" size={11}/>{idea}</button>)}</div>
          <div className="generation-controls">
            <label className="field"><span className="field-label">Visual style</span><select value={style} onChange={e=>setStyle(e.target.value)}>{styles.map(x=><option key={x}>{x}</option>)}</select></label>
            <label className="field"><span className="field-label">Aspect ratio</span><select value={ratio} onChange={e=>setRatio(e.target.value)}>{ratios.map(x=><option key={x}>{x}</option>)}</select></label>
            <label className="field"><span className="field-label">Outputs</span><select value={count} onChange={e=>setCount(Number(e.target.value))}>{[1,2,3,4].map(x=><option key={x}>{x} {x===1?"image":"images"}</option>)}</select></label>
          </div>
          {brands.length>0&&<label className="field"><span className="field-label">Brand consistency <small className="field-hint">Optional</small></span><select value={brand} onChange={e=>setBrand(e.target.value)}><option value="">No brand profile</option>{brands.map(b=><option value={b.id} key={b.id}>{b.name}</option>)}</select></label>}
          {error&&<InlineNotice tone="error">{error}</InlineNotice>}
          <button className="button full generate-button" disabled={!prompt.trim()||running}>{running?<><LoadingDots/> Creating your images</>:<><Icon name="sparkles" size={17}/>Generate {count>1?`${count} images`:"image"}</>}</button>
        </div>
      </form>

      <aside className="card generation-preview">
        <div className="card-header"><h2>Generation status</h2><StatusBadge status={job?.status??"Ready"}/></div>
        <div className={running?"preview-stage active":"preview-stage"}>
          {job?.status==="completed"&&job.assets?.[0]?<img src={job.assets[0].delivery_url} alt="Latest generated asset"/>:<><span className="preview-orb"><Icon name={running?"wand":"image"} size={27}/></span><h3>{running?"Bringing your idea to life…":"Your canvas is ready"}</h3><p>{running?"You can keep exploring the studio while this finishes.":"Describe an image and your latest result will appear here."}</p>{running&&<div className="progress-track"><span/></div>}</>}
        </div>
        <div className="preview-foot"><span><Icon name="shield" size={14}/> Outputs save automatically</span>{job?.error_message&&<small>{job.error_message}</small>}</div>
      </aside>
    </div>

    <div className="section-heading"><div><h2>Recent creations</h2><p>Your reusable media library</p></div>{history.length>0&&<Link href="/editor" className="text-link">View in editor <Icon name="arrow" size={14}/></Link>}</div>
    {loading?<div className="history-skeleton">{[1,2,3,4].map(x=><i key={x}/>)}</div>:history.length?<div className="media-grid creation-grid">{history.map((asset,index)=><article className="asset-card" key={asset.id}><div className="asset-image"><img src={asset.delivery_url} alt={`Generated asset ${index+1}`}/><div className="asset-actions"><Link href="/editor" aria-label="Edit asset"><Icon name="sliders" size={15}/></Link><Link href="/publish" aria-label="Publish asset"><Icon name="send" size={15}/></Link></div></div><div className="asset-meta"><span>{asset.width&&asset.height?`${asset.width} × ${asset.height}`:"AI image"}</span><span>Ready</span></div></article>)}</div>:<div className="card"><EmptyState icon="sparkles" title="Your first creation starts here" description="Write a prompt above. Every generated image is saved here automatically and stays ready to edit or publish."/></div>}
  </div><style>{`
    .sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
    .connector-banner{display:grid;grid-template-columns:auto 1fr minmax(280px,430px);gap:16px;align-items:center;margin-bottom:18px;padding:15px 17px;border-color:rgba(155,122,255,.22);background:linear-gradient(100deg,rgba(155,122,255,.09),rgba(255,92,157,.035))}.connector-icon{display:grid;place-items:center;width:42px;height:42px;border-radius:12px;background:rgba(155,122,255,.13);color:#c5b4ff}.connector-title{display:flex;gap:10px;align-items:center}.connector-title h2{margin:0;font-size:14px}.connector-banner p{margin:4px 0 0;color:var(--muted);font-size:10px}.connector-banner form{display:flex;gap:8px}.connector-banner input{min-width:0}.connector-banner .button{white-space:nowrap}
    .creator-layout{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(330px,.85fr);gap:18px}.card-kicker{margin:0 0 4px;color:var(--pink);font-size:9px;font-weight:800;letter-spacing:.13em}.prompt-card .card-header h2{font-size:17px}.shortcut{padding:5px 8px;border:1px solid var(--line);border-radius:6px;color:var(--muted-2);font-size:9px}.prompt-card textarea{min-height:154px}.generation-controls{display:grid;grid-template-columns:1.4fr 1fr .8fr;gap:10px}.generate-button{margin-top:2px;min-height:48px}.generation-preview{overflow:hidden}.preview-stage{display:grid;place-items:center;align-content:center;min-height:385px;padding:34px;text-align:center;background:radial-gradient(circle at 50% 42%,rgba(155,122,255,.13),transparent 10rem),#0b0c11}.preview-stage img{width:100%;height:100%;max-height:430px;object-fit:contain}.preview-stage.active{background:radial-gradient(circle at 50% 42%,rgba(255,92,157,.17),transparent 11rem),#0b0c11}.preview-orb{display:grid;place-items:center;width:61px;height:61px;margin-bottom:15px;border:1px solid rgba(255,255,255,.1);border-radius:20px;background:rgba(255,255,255,.04);color:#c8b9f5;box-shadow:0 18px 50px rgba(0,0,0,.3)}.preview-stage.active .preview-orb{animation:pulse 1.8s infinite}@keyframes pulse{50%{transform:scale(1.05);box-shadow:0 0 0 10px rgba(255,92,157,.04)}}.preview-stage h3{margin:0 0 7px;font-size:14px}.preview-stage p{max-width:290px;margin:0;color:var(--muted);font-size:11px;line-height:1.55}.progress-track{width:min(240px,80%);height:4px;margin-top:22px;overflow:hidden;border-radius:99px;background:#22232c}.progress-track span{display:block;width:45%;height:100%;border-radius:99px;background:linear-gradient(90deg,var(--pink),var(--violet));animation:progress 1.5s infinite ease-in-out}@keyframes progress{from{transform:translateX(-100%)}to{transform:translateX(260%)}}.preview-foot{display:flex;justify-content:space-between;gap:12px;padding:13px 16px;border-top:1px solid var(--line);color:var(--muted-2);font-size:9px}.preview-foot span{display:flex;align-items:center;gap:6px}.text-link{display:inline-flex;align-items:center;gap:5px;color:#c9c4d0;font-size:11px;text-decoration:none}.text-link:hover{color:#fff}.asset-image{position:relative;overflow:hidden}.asset-image>img{transition:transform .35s}.asset-card:hover .asset-image>img{transform:scale(1.025)}.asset-actions{position:absolute;right:8px;bottom:8px;display:flex;gap:5px;opacity:0;transform:translateY(3px);transition:.18s}.asset-card:hover .asset-actions,.asset-card:focus-within .asset-actions{opacity:1;transform:none}.asset-actions a{display:grid;place-items:center;width:32px;height:32px;border:1px solid rgba(255,255,255,.15);border-radius:9px;background:rgba(10,10,14,.84);color:#fff;backdrop-filter:blur(8px)}.history-skeleton{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.history-skeleton i{aspect-ratio:1;border-radius:14px;background:linear-gradient(100deg,#12131a 30%,#1b1c24 50%,#12131a 70%);background-size:300% 100%;animation:shimmer 1.5s infinite}@keyframes shimmer{to{background-position:-150% 0}}
    @media(max-width:1000px){.creator-layout{grid-template-columns:1fr}.connector-banner{grid-template-columns:auto 1fr}.connector-banner form{grid-column:1/-1}.preview-stage{min-height:300px}}
    @media(max-width:640px){.connector-banner{grid-template-columns:1fr}.connector-icon{display:none}.connector-banner form{display:grid}.connector-title{align-items:flex-start;justify-content:space-between}.generation-controls{grid-template-columns:1fr 1fr}.generation-controls .field:last-child{grid-column:1/-1}.history-skeleton{grid-template-columns:repeat(2,1fr)}.asset-actions{opacity:1;transform:none}.preview-stage{min-height:260px}}
  `}</style></main>;
}
