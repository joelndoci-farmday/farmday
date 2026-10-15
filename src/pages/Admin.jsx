import React,{useState,useEffect} from 'react';
import {supabase} from '../lib/supabase';
import {yt} from '../lib/youtube';
import SafetyReview from '../components/SafetyReview';
import Analytics from '../components/Analytics';
import YouTubeConnection from '../components/YouTubeConnection';
import VideoWorkflow from '../components/VideoWorkflow';
import AdminVideoAgreements from '../components/AdminVideoAgreements';
import AdminTeam from '../components/AdminTeam';
const QUEUES=[['unassigned','Unassigned'],['monetization','Monetization queue'],['non_monetization','Non-monetized queue']];
export default function Admin(){
 const [items,setItems]=useState([]),[reviews,setReviews]=useState({}),[queue,setQueue]=useState('unassigned'),[message,setMessage]=useState(''),[busy,setBusy]=useState(false);
 async function load(){const [{data,error},{data:meta,error:metaError}]=await Promise.all([supabase.from('videos').select('*').order('created_at',{ascending:false}),supabase.from('farmday_video_reviews').select('*')]);setItems(data||[]);setReviews(Object.fromEntries((meta||[]).map(x=>[x.video_id,x])));if(error||metaError)setMessage(error?.message||metaError?.message)}useEffect(()=>{load()},[]);
 async function assign(id,next){if(!window.confirm(`Move this video to ${next.replaceAll('_',' ')}? This does NOT publish it.`))return;setBusy(true);const{error}=await supabase.from('farmday_video_reviews').update({queue:next,updated_at:new Date().toISOString()}).eq('video_id',id);setBusy(false);setMessage(error?error.message:'Video moved to review queue. No YouTube publishing occurred.');load()}
 async function change(id,status){if(!window.confirm(`${status==='approved'?'Approve for public display on Farmday':'Reject'} this video? This does NOT upload to YouTube.`))return;setBusy(true);const{error}=await supabase.from('videos').update({status}).eq('id',id);setBusy(false);setMessage(error?error.message:'Farmday visibility updated. YouTube was not changed.');load()}
 const filtered=items.filter(v=>(reviews[v.id]?.queue||'unassigned')===queue);
 return <main className="wrap section farmday-admin-dashboard">
  <header className="farmday-admin-intro"><div><p className="muted">FARMDAY · CONTROL CENTER</p><h1 className="pageTitle">Admin dashboard</h1><p className="muted">Review, publish and manage videos. Advanced tools are organized below.</p></div></header>
  <YouTubeConnection compact/>
  <VideoWorkflow/>
  <section className="farmday-admin-secondary"><h2>Additional administration</h2><p className="muted">Open a section only when you need it. These tools do not publish videos.</p>
   <details><summary>Safety & copyright review</summary><SafetyReview/></details>
   <details><summary>YouTube connection & settings</summary><YouTubeConnection/></details>
   <details><summary>Administrators & permissions</summary><AdminTeam/></details>
   <details><summary>Video agreements</summary><AdminVideoAgreements/></details>
   <details><summary>Analytics</summary><Analytics/></details>
   <details><summary>Legacy video queues</summary><p className="muted">Older FarmDay-only queues; they do not change YouTube publication status.</p><div className="queue-tabs">{QUEUES.map(([key,label])=><button key={key} className="btn outline" aria-pressed={queue===key} onClick={()=>setQueue(key)}>{label} ({items.filter(v=>(reviews[v.id]?.queue||'unassigned')===key).length})</button>)}</div>{message&&<div className="notice">{message}</div>}<div className="adminlist">{filtered.length===0?<div className="empty">No videos in this queue.</div>:filtered.map(v=><div className="adminrow" key={v.id}><img src={`https://img.youtube.com/vi/${v.youtube_video_id}/mqdefault.jpg`} alt="Video thumbnail"/><div><b>{v.title}</b><p className="muted">FarmDay status: {v.status} · <a href={yt(v.youtube_video_id)} target="_blank" rel="noreferrer">Open on YouTube</a></p></div><div className="rowactions"><button disabled={busy} onClick={()=>change(v.id,'approved')} className="btn outline">Approve on FarmDay only</button></div></div>)}</div></details>
  </section>
 </main>;
}
