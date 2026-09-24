"use client";

import Link from "next/link";
import {FormEvent, useEffect, useState} from "react";
import {EmptyState, Icon, InlineNotice, LoadingDots, PageHeader} from "../../components/StudioUI";

type Draft={id:string;caption:string;hashtags:string[];settings_json:{tone:string;cta:string;length:string;emojis:boolean}};
const api=process.env.NEXT_PUBLIC_API_URL??"http://localhost:8000";
const tones=["Professional","Playful","Bold","Educational","Luxury"];
const ctas=["Ask a question","Visit link in bio","Save this post","Shop now","No CTA"];

export default function Captions(){
  const[text,setText]=useState(""),[tone,setTone]=useState(tones[1]),[cta,setCta]=useState(ctas[0]),[length,setLength]=useState("short"),[emojis,setEmojis]=useState(true),[drafts,setDrafts]=useState<Draft[]>([]),[result,setResult]=useState<Draft|null>(null),[error,setError]=useState(""),[busy,setBusy]=useState(false),[copied,setCopied]=useState("");
  const auth=()=>({token:localStorage.getItem("instahub_access_token"),workspace:localStorage.getItem("instahub_workspace_id")});
  useEffect(()=>{const{token,workspace}=auth();if(token&&workspace)fetch(api+"/v1/workspaces/"+workspace+"/captions",{headers:{Authorization:"Bearer "+token}}).then(r=>r.ok?r.json():[]).then(rows=>{setDrafts(rows);if(rows[0])setResult(rows[0])})},[]);

  async function generate(e?:FormEvent){
    e?.preventDefault();setError("");setBusy(true);const{token,workspace}=auth();
    if(!token||!workspace){setError("Sign in and select a workspace first.");setBusy(false);return}
    const r=await fetch(api+"/v1/captions",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+token},body:JSON.stringify({workspace_id:workspace,source_text:text,tone,cta,length,emojis})});
    if(!r.ok){setError((await r.json()).detail??"Could not generate caption.");setBusy(false);return}
    const draft=await r.json();setResult(draft);setDrafts(items=>[draft,...items]);setBusy(false);
  }
  async function copy(value:string,name:string){await navigator.clipboard.writeText(value);setCopied(name);setTimeout(()=>setCopied(""),1600)}

  return <main><div className="page captions-page">
    <PageHeader eyebrow="Caption Assistant" title="Find the words." accent="Keep your voice." description="Turn a simple brief into an Instagram-ready caption, focused CTA, and a clean hashtag set." actions={<Link className="button secondary" href="/brand-studio"><Icon name="palette" size={16}/>Brand voice</Link>}/>
    <div className="caption-layout">
      <form className="card caption-form" onSubmit={generate}>
        <div className="card-header"><div><p className="card-kicker">CONTENT BRIEF</p><h2>What is this post about?</h2></div><span className="step-count">1 of 2</span></div>
        <div className="card-body stack">
          <label className="field"><span className="field-label">Describe the post <small className="char-count">{text.length} characters</small></span><textarea value={text} onChange={e=>setText(e.target.value)} required placeholder="We’re launching a sustainable running shoe made from recycled ocean plastic…"/></label>
          <div className="caption-controls">
            <label className="field"><span className="field-label">Tone</span><select value={tone} onChange={e=>setTone(e.target.value)}>{tones.map(x=><option key={x}>{x}</option>)}</select></label>
            <label className="field"><span className="field-label">Call to action</span><select value={cta} onChange={e=>setCta(e.target.value)}>{ctas.map(x=><option key={x}>{x}</option>)}</select></label>
          </div>
          <div className="preference-row"><div><span className="field-label">Caption length</span><div className="segmented"><button type="button" className={length==="short"?"active":""} onClick={()=>setLength("short")}>Short</button><button type="button" className={length==="long"?"active":""} onClick={()=>setLength("long")}>Long</button></div></div><label className="emoji-switch"><span><b>Include emojis</b><small>Add a little visual energy</small></span><input type="checkbox" checked={emojis} onChange={e=>setEmojis(e.target.checked)}/><i/></label></div>
          {error&&<InlineNotice tone="error">{error}</InlineNotice>}
          <button className="button full" disabled={busy||!text.trim()}>{busy?<><LoadingDots/>Writing your caption</>:<><Icon name="sparkles" size={16}/>Generate caption</>}</button>
        </div>
      </form>

      <section className="card result-card" aria-live="polite">
        <div className="card-header"><div><p className="card-kicker">DRAFT</p><h2>{result?"Ready to post":"Your result"}</h2></div>{result&&<div className="result-actions"><button className="icon-button" onClick={()=>generate()} title="Regenerate" aria-label="Regenerate caption"><Icon name="refresh" size={15}/></button><button className="icon-button" onClick={()=>copy(`${result.caption}\n\n${result.hashtags.join(" ")}`,"all")} title="Copy all" aria-label="Copy caption and hashtags"><Icon name={copied==="all"?"check":"copy"} size={15}/></button></div>}</div>
        {result?<div className="result-body"><div className="caption-copy"><p>{result.caption}</p><span>{result.caption.length} / 2,200</span></div><div className="hashtags"><div><b>Hashtags</b><button onClick={()=>copy(result.hashtags.join(" "),"tags")}><Icon name={copied==="tags"?"check":"copy"} size={13}/>{copied==="tags"?"Copied":"Copy"}</button></div><p>{result.hashtags.join(" ")}</p></div><div className="result-meta"><span>{result.settings_json.tone}</span><span>{result.settings_json.length}</span><span>{result.settings_json.cta}</span></div><Link className="button full secondary" href="/publish">Continue to publish <Icon name="arrow" size={15}/></Link></div>:<EmptyState icon="text" title="A polished draft will appear here" description="Give the assistant a clear content brief and choose the voice you want to use."/>}
      </section>
    </div>

    <div className="section-heading"><div><h2>Caption history</h2><p>Reuse or adapt an earlier idea</p></div><span className="history-count">{drafts.length} saved</span></div>
    {drafts.length?<div className="draft-list">{drafts.map((draft,index)=><button className={result?.id===draft.id?"draft-row active":"draft-row"} onClick={()=>setResult(draft)} key={draft.id}><span className="draft-number">{String(index+1).padStart(2,"0")}</span><div><p>{draft.caption}</p><small>{draft.hashtags.slice(0,4).join(" ")}</small></div><span className="draft-tone">{draft.settings_json.tone}</span><Icon name="arrow" size={15}/></button>)}</div>:<div className="card"><EmptyState icon="text" title="No caption history yet" description="Generated drafts are saved automatically so you can revisit the strongest ideas."/></div>}
  </div><style>{`
    .caption-layout{display:grid;grid-template-columns:minmax(0,1fr) minmax(360px,.82fr);gap:18px;align-items:start}.card-kicker{margin:0 0 4px;color:var(--pink);font-size:9px;font-weight:800;letter-spacing:.15em}.step-count,.history-count{color:var(--muted);font-size:10px}.caption-form textarea{min-height:185px}.caption-controls{display:grid;grid-template-columns:1fr 1fr;gap:10px}.preference-row{display:grid;grid-template-columns:1fr 1.1fr;gap:12px;align-items:end}.preference-row>div{display:grid;gap:7px}.emoji-switch{position:relative;display:flex;justify-content:space-between;align-items:center;min-height:59px;padding:10px 12px;border:1px solid var(--line);border-radius:11px;background:#0c0d12}.emoji-switch>span{display:grid;gap:2px}.emoji-switch b{font-size:11px}.emoji-switch small{color:var(--muted);font-size:9px}.emoji-switch input{position:absolute;opacity:0}.emoji-switch i{position:relative;width:35px;height:20px;border-radius:99px;background:#34333b;transition:.18s}.emoji-switch i::after{content:"";position:absolute;top:3px;left:3px;width:14px;height:14px;border-radius:50%;background:#aaa7b1;transition:.18s}.emoji-switch input:checked+i{background:linear-gradient(90deg,var(--pink),var(--violet))}.emoji-switch input:checked+i::after{left:18px;background:#fff}.result-card{position:sticky;top:24px;overflow:hidden}.result-actions{display:flex;gap:6px}.result-body{display:grid;gap:14px;padding:20px}.caption-copy{position:relative;padding:16px;border:1px solid var(--line);border-radius:12px;background:#0c0d12}.caption-copy p{margin:0;color:#e5e1e8;font-family:Georgia,serif;font-size:16px;line-height:1.65;white-space:pre-wrap}.caption-copy>span{display:block;margin-top:12px;color:var(--muted-2);font-size:9px;text-align:right}.hashtags{padding:13px;border:1px solid rgba(155,122,255,.13);border-radius:11px;background:rgba(155,122,255,.045)}.hashtags>div{display:flex;justify-content:space-between;align-items:center}.hashtags b{font-size:10px}.hashtags button{display:flex;gap:5px;align-items:center;border:0;background:none;color:#b9aadf;font-size:9px}.hashtags p{margin:9px 0 0;color:#a997d3;font-size:11px;line-height:1.55}.result-meta{display:flex;gap:6px;flex-wrap:wrap}.result-meta span{padding:5px 8px;border:1px solid var(--line);border-radius:99px;color:var(--muted);font-size:9px;text-transform:capitalize}.draft-list{display:grid;border:1px solid var(--line);border-radius:14px;background:var(--surface);overflow:hidden}.draft-row{display:grid;grid-template-columns:auto 1fr auto auto;gap:14px;align-items:center;padding:14px 16px;border:0;border-bottom:1px solid var(--line);background:transparent;color:var(--muted);text-align:left}.draft-row:last-child{border:0}.draft-row:hover,.draft-row.active{background:rgba(255,255,255,.025)}.draft-row.active{box-shadow:inset 3px 0 var(--pink)}.draft-number{color:var(--muted-2);font-size:9px}.draft-row div{min-width:0}.draft-row p{overflow:hidden;margin:0 0 4px;color:#d5d1da;font-size:11px;text-overflow:ellipsis;white-space:nowrap}.draft-row small{display:block;overflow:hidden;max-width:520px;text-overflow:ellipsis;white-space:nowrap;font-size:9px}.draft-tone{padding:5px 8px;border:1px solid var(--line);border-radius:99px;font-size:9px}
    @media(max-width:1050px){.caption-layout{grid-template-columns:1fr}.result-card{position:static}}@media(max-width:620px){.caption-controls,.preference-row{grid-template-columns:1fr}.draft-row{grid-template-columns:auto 1fr auto}.draft-tone{display:none}}
  `}</style></main>;
}
