"use client";

import Link from "next/link";
import {useEffect, useMemo, useState} from "react";
import {EmptyState, Icon, InlineNotice, LoadingDots, PageHeader, StatusBadge} from "../../components/StudioUI";

type Asset={id:string;delivery_url:string;media_type:string};type Board={id:string;name:string};
const api=process.env.NEXT_PUBLIC_API_URL??"http://localhost:8000";

export default function Publish(){
  const[assets,setAssets]=useState<Asset[]>([]),[asset,setAsset]=useState(""),[platform,setPlatform]=useState("instagram"),[caption,setCaption]=useState(""),[boards,setBoards]=useState<Board[]>([]),[board,setBoard]=useState(""),[title,setTitle]=useState(""),[state,setState]=useState("ready"),[detail,setDetail]=useState(""),[loading,setLoading]=useState(true);
  const auth=()=>({token:localStorage.getItem("instahub_access_token"),workspace:localStorage.getItem("instahub_workspace_id")});
  const current=useMemo(()=>assets.find(item=>item.id===asset),[assets,asset]);
  const busy=["queueing","publishing","processing"].includes(state.toLowerCase());
  useEffect(()=>{const{token,workspace}=auth();if(token&&workspace)fetch(api+`/v1/workspaces/${workspace}/assets`,{headers:{Authorization:"Bearer "+token}}).then(r=>r.ok?r.json():[]).then(rows=>{setAssets(rows);if(rows[0])setAsset(rows[0].id)}).finally(()=>setLoading(false));else setLoading(false)},[]);
  useEffect(()=>{if(platform!=="pinterest")return;const{token,workspace}=auth();if(token&&workspace)fetch(api+`/v1/pinterest/boards?workspace_id=${workspace}`,{headers:{Authorization:"Bearer "+token}}).then(r=>r.ok?r.json():[]).then(setBoards)},[platform]);

  async function publish(){
    const{token,workspace}=auth();if(!token||!workspace){setState("failed");setDetail("Sign in and select a workspace first.");return}
    setState("queueing");setDetail("Preparing your media…");
    const r=await fetch(api+"/v1/posts",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+token},body:JSON.stringify({workspace_id:workspace,media_asset_id:asset,caption,platform,board_id:platform==="pinterest"?board:null,title})});const value=await r.json();
    if(!r.ok){setState("failed");setDetail(value.detail??"Check the connected account and try again.");return}
    setState("publishing");setDetail("Attempt started with automatic retries.");
    const poll=setInterval(async()=>{const result=await fetch(api+`/v1/posts/${value.post_id}`,{headers:{Authorization:"Bearer "+token}});if(!result.ok)return;const post=await result.json();setState(post.status);setDetail(post.attempts[0]?.error_message??(post.status==="published"?"Your post is live.":"Processing media…"));if(["published","failed"].includes(post.status))clearInterval(poll)},1800);
  }

  return <main><div className="page publish-page">
    <PageHeader eyebrow="Publish Desk" title="Ready when" accent="you are." description="Choose your strongest asset, tailor the copy for each channel, and publish with a clear view of what your audience will see." actions={<Link href="/schedule" className="button secondary"><Icon name="calendar" size={16}/>Schedule instead</Link>}/>
    {loading?<div className="publish-skeleton"><i/><i/></div>:assets.length===0?<div className="card"><EmptyState icon="image" title="You need an image before publishing" description="Generate an asset first. It will be saved to this publishing desk automatically." action={<Link className="button" href="/"><Icon name="sparkles" size={15}/>Create an image</Link>}/></div>:<div className="publish-layout">
      <section className="card media-panel">
        <div className="card-header"><div><h2>Select media</h2><small>{assets.length} ready to publish</small></div><StatusBadge status="Ready"/></div>
        <div className="publish-preview">{current&&<img src={current.delivery_url} alt="Selected media preview"/>}<span className="preview-channel"><Icon name={platform==="instagram"?"instagram":"pinterest"} size={14}/>{platform}</span></div>
        <div className="media-strip" aria-label="Media library">{assets.map((item,index)=><button className={asset===item.id?"media-tile selected":"media-tile"} onClick={()=>setAsset(item.id)} key={item.id} aria-label={`Select media ${index+1}`}><img src={item.delivery_url} alt={`Media ${index+1}`}/></button>)}</div>
      </section>

      <section className="card composer-panel">
        <div className="card-header"><div><p className="card-kicker">POST DETAILS</p><h2>Compose your post</h2></div><StatusBadge status={state}/></div>
        <div className="card-body stack">
          <div className="field"><span className="field-label">Channel</span><div className="channel-picker">{["instagram","pinterest"].map(value=><button type="button" className={platform===value?"active":""} onClick={()=>{setPlatform(value);setState("ready");setDetail("")}} key={value}><Icon name={value==="instagram"?"instagram":"pinterest"} size={17}/><span>{value}<small>{value==="instagram"?"Feed post":"Standard Pin"}</small></span>{platform===value&&<Icon name="check" size={15}/>}</button>)}</div></div>
          {platform==="pinterest"&&<><label className="field"><span className="field-label">Board</span><select value={board} onChange={e=>setBoard(e.target.value)} required><option value="">Choose a board</option>{boards.map(item=><option value={item.id} key={item.id}>{item.name}</option>)}</select></label><label className="field"><span className="field-label">Pin title <small className="char-count">{title.length}/100</small></span><input value={title} onChange={e=>setTitle(e.target.value)} maxLength={100} placeholder="A clear, searchable title"/></label></>}
          <label className="field"><span className="field-label">Caption <small className="char-count">{caption.length}/2,200</small></span><textarea value={caption} onChange={e=>setCaption(e.target.value)} maxLength={2200} placeholder="Tell the story behind this post…"/></label>
          <div className="composer-tools"><Link href="/captions"><Icon name="sparkles" size={13}/>Write with AI</Link><span>Alt text will use asset metadata</span></div>
          {detail&&<InlineNotice tone={state==="failed"?"error":state==="published"?"success":"info"}>{busy&&<LoadingDots/>} {detail}</InlineNotice>}
          <button className="button full publish-button" disabled={!asset||busy||(platform==="pinterest"&&!board)} onClick={publish}>{busy?<><LoadingDots/>Publishing</>:state==="published"?<><Icon name="check" size={16}/>Published</>:<><Icon name="send" size={16}/>Publish to {platform}<Icon name="arrow" size={15}/></>}</button>
          <p className="publish-note"><Icon name="shield" size={13}/>You’ll see a final status here. Failed attempts include diagnostics and can be retried safely.</p>
        </div>
      </section>
    </div>}
  </div><style>{`
    .publish-layout{display:grid;grid-template-columns:minmax(0,1.05fr) minmax(370px,.95fr);gap:18px;align-items:start}.media-panel{overflow:hidden}.media-panel .card-header>div{display:grid;gap:3px}.media-panel .card-header small{color:var(--muted);font-size:9px}.publish-preview{position:relative;display:grid;place-items:center;min-height:470px;padding:18px;background:radial-gradient(circle,#191921,#090a0e 70%)}.publish-preview img{display:block;max-width:100%;max-height:520px;object-fit:contain;border-radius:7px;box-shadow:0 20px 55px #0008}.preview-channel{position:absolute;left:13px;bottom:13px;display:flex;align-items:center;gap:6px;padding:7px 9px;border:1px solid rgba(255,255,255,.12);border-radius:9px;background:rgba(10,10,14,.8);color:#ddd8e2;font-size:9px;text-transform:capitalize;backdrop-filter:blur(10px)}.media-strip{display:grid;grid-template-columns:repeat(7,1fr);gap:7px;padding:12px;border-top:1px solid var(--line);overflow:auto}.media-strip .media-tile{min-width:58px}.composer-panel{position:sticky;top:24px}.card-kicker{margin:0 0 4px;color:var(--pink);font-size:9px;font-weight:800;letter-spacing:.15em}.channel-picker{display:grid;grid-template-columns:1fr 1fr;gap:8px}.channel-picker button{display:grid;grid-template-columns:auto 1fr auto;gap:9px;align-items:center;padding:11px;border:1px solid var(--line);border-radius:11px;background:#0c0d12;color:var(--muted);text-align:left;text-transform:capitalize}.channel-picker button>span{display:grid;gap:2px;color:#cbc6d0;font-size:11px}.channel-picker small{color:var(--muted-2);font-size:8px}.channel-picker button.active{border-color:rgba(255,92,157,.38);background:rgba(255,92,157,.06);color:var(--pink-soft)}.composer-panel textarea{min-height:160px}.composer-tools{display:flex;justify-content:space-between;gap:10px;align-items:center;margin-top:-5px;color:var(--muted-2);font-size:9px}.composer-tools a{display:flex;align-items:center;gap:5px;color:#c9b6ff;text-decoration:none}.publish-button{min-height:49px;text-transform:capitalize}.publish-note{display:flex;align-items:flex-start;gap:7px;margin:0;color:var(--muted-2);font-size:9px;line-height:1.5}.publish-note svg{flex:0 0 auto}.publish-skeleton{display:grid;grid-template-columns:1fr 1fr;gap:18px}.publish-skeleton i{height:650px;border-radius:16px;background:linear-gradient(100deg,#111219 30%,#191a22 50%,#111219 70%);background-size:300%;animation:shimmer 1.4s infinite}
    @media(max-width:1050px){.publish-layout{grid-template-columns:1fr}.composer-panel{position:static}.publish-preview{min-height:370px}.publish-skeleton{grid-template-columns:1fr}}@media(max-width:600px){.publish-preview{min-height:320px;padding:10px}.media-strip{grid-template-columns:repeat(5,1fr)}.channel-picker{grid-template-columns:1fr}.composer-tools span{display:none}}
  `}</style></main>;
}
