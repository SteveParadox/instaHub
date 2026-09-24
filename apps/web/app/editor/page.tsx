"use client";

import Link from "next/link";
import {useEffect, useState} from "react";
import {EmptyState, Icon, InlineNotice, LoadingDots, PageHeader, StatusBadge, type IconName} from "../../components/StudioUI";

type Asset={id:string;delivery_url:string;width?:number;height?:number};
type Op={id:string;status:string;variant_id?:string;error_message?:string};
const api=process.env.NEXT_PUBLIC_API_URL??"http://localhost:8000";
const tools:{operation:string;label:string;hint:string;icon:IconName;extra?:Record<string,unknown>;needsPrompt?:boolean}[]=[
  {operation:"variation",label:"Create variation",hint:"A fresh take on this image",icon:"layers"},
  {operation:"edit",label:"Prompt edit",hint:"Change it with natural language",icon:"wand",needsPrompt:true},
  {operation:"background_remove",label:"Remove background",hint:"Export a clean cutout",icon:"image"},
  {operation:"upscale",label:"Upscale 2×",hint:"Increase resolution and detail",icon:"expand",extra:{factor:2}},
  {operation:"crop",label:"Instagram crop",hint:"Portrait 4:5 composition",icon:"crop",extra:{aspect_ratio:"4:5"}},
];

export default function Editor(){
  const[assets,setAssets]=useState<Asset[]>([]),[selected,setSelected]=useState<Asset|null>(null),[prompt,setPrompt]=useState(""),[status,setStatus]=useState("ready"),[variants,setVariants]=useState<Asset[]>([]),[loading,setLoading]=useState(true),[error,setError]=useState("");
  const auth=()=>({token:localStorage.getItem("instahub_access_token"),workspace:localStorage.getItem("instahub_workspace_id")});
  const busy=["queued","processing","retrying"].includes(status);

  useEffect(()=>{const{token,workspace}=auth();if(!token||!workspace){setLoading(false);return}fetch(api+"/v1/workspaces/"+workspace+"/assets",{headers:{Authorization:"Bearer "+token}}).then(r=>r.ok?r.json():[]).then(rows=>{setAssets(rows);if(rows[0])setSelected(rows[0])}).finally(()=>setLoading(false))},[]);
  useEffect(()=>{if(!selected)return;const{token}=auth();setVariants([]);fetch(api+"/v1/assets/"+selected.id+"/variants",{headers:{Authorization:"Bearer "+token}}).then(r=>r.ok?r.json():[]).then(setVariants)},[selected]);

  async function run(operation:string,extra:Record<string,unknown>={}){
    if(!selected)return;setStatus("queued");setError("");const{token}=auth();
    const r=await fetch(api+"/v1/assets/"+selected.id+"/operations",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+token},body:JSON.stringify({operation,prompt,...extra})});
    if(!r.ok){setStatus("failed");setError((await r.json()).detail??"The edit could not be started.");return}
    const op:Op=await r.json();
    const t=setInterval(async()=>{const n=await fetch(api+"/v1/asset-operations/"+op.id,{headers:{Authorization:"Bearer "+token}});if(n.ok){const value:Op=await n.json();setStatus(value.status);if(["completed","failed"].includes(value.status)){clearInterval(t);if(value.status==="failed")setError(value.error_message??"The edit failed. Try another instruction.");if(value.status==="completed")fetch(api+"/v1/assets/"+selected.id+"/variants",{headers:{Authorization:"Bearer "+token}}).then(response=>response.json()).then(setVariants)}}},1800);
  }

  return <main><div className="page editor-page">
    <PageHeader eyebrow="Image Editor" title="Refine every" accent="detail." description="Create variations, clean up backgrounds, resize for Instagram, and keep every version tied to its original." actions={<Link href="/" className="button secondary"><Icon name="plus" size={16}/>Create new</Link>}/>

    {loading?<div className="editor-loading"><i/><i/></div>:assets.length===0?<div className="card"><EmptyState icon="image" title="No images to edit yet" description="Generate your first image, then come back here to create polished versions." action={<Link className="button" href="/"><Icon name="sparkles" size={15}/>Create an image</Link>}/></div>:<div className="editor-shell">
      <section className="card asset-browser">
        <div className="card-header"><div><h2>Media library</h2><small>{assets.length} {assets.length===1?"asset":"assets"}</small></div><span className="library-hint">Select one to edit</span></div>
        <div className="card-body"><div className="media-grid">{assets.map((asset,index)=><button type="button" className={selected?.id===asset.id?"media-tile selected":"media-tile"} onClick={()=>setSelected(asset)} key={asset.id} aria-label={`Edit asset ${index+1}`}><img src={asset.delivery_url} alt={`Media asset ${index+1}`}/></button>)}</div></div>
      </section>

      <section className="edit-workspace">
        <div className="canvas-card card">
          <div className="canvas-toolbar"><StatusBadge status={status}/><span>{selected?.width&&selected?.height?`${selected.width} × ${selected.height}`:"Original asset"}</span></div>
          <div className="canvas">{selected?<img src={selected.delivery_url} alt="Selected asset for editing"/>:<EmptyState title="Choose an asset" description="Select media from your library to start editing."/>}</div>
        </div>
        <div className="card tools-panel">
          <div className="card-header"><div><p className="card-kicker">EDIT TOOLS</p><h2>What should change?</h2></div>{busy&&<LoadingDots/>}</div>
          <div className="card-body stack">
            <label className="field"><span className="field-label">Edit instruction <small className="field-hint">Used for prompt edit</small></span><textarea value={prompt} onChange={e=>setPrompt(e.target.value)} placeholder="Make the backdrop warmer, add soft afternoon shadows…"/></label>
            <div className="tool-grid">{tools.map(tool=><button type="button" className="tool-button" disabled={busy||!selected||(tool.needsPrompt&&!prompt.trim())} onClick={()=>run(tool.operation,tool.extra)} key={tool.operation}><span><Icon name={tool.icon} size={17}/></span><div><b>{tool.label}</b><small>{tool.hint}</small></div><Icon name="arrow" size={14}/></button>)}</div>
            {error&&<InlineNotice tone="error">{error}</InlineNotice>}
          </div>
        </div>
      </section>
    </div>}

    {selected&&<><div className="section-heading"><div><h2>Saved versions</h2><p>Every edit remains connected to the original</p></div><StatusBadge status={`${variants.length} versions`}/></div>{variants.length?<div className="media-grid">{variants.map((variant,index)=><article className="asset-card" key={variant.id}><img src={variant.delivery_url} alt={`Saved variant ${index+1}`}/><div className="asset-meta"><span>Version {variants.length-index}</span><span>Saved</span></div></article>)}</div>:<div className="card"><EmptyState icon="layers" title="No saved versions yet" description="Choose an edit tool above. Your results will appear here without replacing the original."/></div>}</>}
  </div><style>{`
    .editor-shell{display:grid;grid-template-columns:minmax(280px,.68fr) minmax(520px,1.32fr);gap:18px;align-items:start}.asset-browser{position:sticky;top:24px;max-height:calc(100vh - 48px);overflow:auto}.asset-browser .card-header>div{display:grid;gap:3px}.asset-browser .card-header small,.library-hint{color:var(--muted);font-size:10px}.asset-browser .media-grid{grid-template-columns:repeat(3,1fr)}.edit-workspace{display:grid;gap:18px}.canvas-card{overflow:hidden}.canvas-toolbar{display:flex;justify-content:space-between;align-items:center;padding:10px 13px;border-bottom:1px solid var(--line);color:var(--muted);font-size:9px}.canvas{display:grid;place-items:center;min-height:460px;padding:18px;background:radial-gradient(circle,#15151d,#0a0b0f 70%)}.canvas img{display:block;max-width:100%;max-height:560px;object-fit:contain;border-radius:6px;box-shadow:0 18px 50px #0008}.card-kicker{margin:0 0 4px;color:var(--pink);font-size:9px;font-weight:800;letter-spacing:.15em}.tool-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}.tool-button{display:grid;grid-template-columns:auto 1fr auto;gap:10px;align-items:center;padding:11px;border:1px solid var(--line);border-radius:11px;background:rgba(255,255,255,.018);color:var(--muted);text-align:left}.tool-button>span{display:grid;place-items:center;width:34px;height:34px;border-radius:9px;background:#25222e;color:var(--pink-soft)}.tool-button div{display:grid;gap:2px}.tool-button b{color:#d8d3dd;font-size:11px}.tool-button small{font-size:9px}.tool-button:not(:disabled):hover{border-color:rgba(255,92,157,.25);background:rgba(255,92,157,.045);transform:translateY(-1px)}.editor-loading{display:grid;grid-template-columns:.7fr 1.3fr;gap:18px}.editor-loading i{min-height:560px;border-radius:16px;background:linear-gradient(100deg,#111219 30%,#191a22 50%,#111219 70%);background-size:300%;animation:shimmer 1.4s infinite}
    @media(max-width:1160px){.editor-shell{grid-template-columns:1fr}.asset-browser{position:static;max-height:none}.asset-browser .media-grid{grid-template-columns:repeat(6,1fr)}.editor-loading{grid-template-columns:1fr}}
    @media(max-width:680px){.asset-browser .media-grid{grid-template-columns:repeat(4,1fr)}.canvas{min-height:330px;padding:10px}.tool-grid{grid-template-columns:1fr}}
  `}</style></main>;
}
