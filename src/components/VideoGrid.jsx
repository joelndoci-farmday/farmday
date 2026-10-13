import React,{useState,useEffect,useRef,useCallback} from 'react';
import {Link} from 'react-router-dom';
import {Play,ArrowRight,Video} from 'lucide-react';
import {supabase} from '../lib/supabase';
import {yt} from '../lib/youtube';
const PAGE_SIZE=12;
function VideoCards({items,home=false}){return <div className={home?'cards home-cards':'cards'}>{items.map(v=><article className="videocard" key={v.id}><a className="video-external" href={yt(v.youtube_video_id)} target="_blank" rel="noopener noreferrer"><div className="thumb"><img loading="lazy" src={`https://img.youtube.com/vi/${v.youtube_video_id}/hqdefault.jpg`} alt={`Thumbnail for ${v.title}`}/><span className="play"><Play fill="currentColor"/></span></div><div className="cardbody"><h3>{v.title}</h3><p>{v.summary||'Watch the story on Farmday'}</p><span>Watch on YouTube <ArrowRight size={15}/></span></div></a><Link className="farmday-discussion" to={'/video/'+v.id}>Comments & Likes on Farmday</Link></article>)}</div>}
function VideoGrid({limit,home=false,infinite=false}){
 const [items,setItems]=useState([]),[loading,setLoading]=useState(true),[more,setMore]=useState(true),[error,setError]=useState('');
 const cursor=useRef(0),fetching=useRef(false),end=useRef(null);
 const fetchNext=useCallback(async()=>{
  if(fetching.current)return;
  fetching.current=true;setLoading(true);setError('');
  const pageSize=limit||PAGE_SIZE;
  const start=cursor.current;
  const {data,error:err}=await supabase.from('videos').select('id,title,summary,youtube_video_id,created_at,status').eq('status','approved').order('created_at',{ascending:false}).order('id',{ascending:false}).range(start,start+pageSize-1);
  if(err){setError(err.message)}else{
   const incoming=data||[];
   setItems(prev=>[...prev,...incoming.filter(v=>!prev.some(p=>p.id===v.id))]);
   cursor.current=start+incoming.length;
   setMore(infinite&&incoming.length===pageSize);
  }
  fetching.current=false;setLoading(false);
 },[limit,infinite]);
 useEffect(()=>{fetchNext()},[fetchNext]);
 useEffect(()=>{if(!infinite||!more||error||!end.current||typeof IntersectionObserver==='undefined')return;
  const observer=new IntersectionObserver(entries=>{if(entries[0]?.isIntersecting&&!fetching.current)fetchNext()},{rootMargin:'650px'});
  observer.observe(end.current);return()=>observer.disconnect();
 },[infinite,more,error,fetchNext,items.length]);
 return <><VideoCards items={items} home={home}/>{!loading&&items.length===0&&!error&&<div className="empty"><Video size={32}/><h3>The first videos are coming!</h3><p>Approved videos will appear here for everyone to watch.</p><Link className="btn primary" to="/upload">Upload Video</Link></div>}{error&&<p role="alert" className="muted">Could not load videos: {error} <button className="btn outline" onClick={fetchNext}>Retry</button></p>}{loading&&<p className="feed-loading" role="status">Loading videos…</p>}{infinite&&more&&!loading&&<div className="feed-more" ref={end}><button className="btn outline" onClick={fetchNext}>Load more videos</button></div>}{infinite&&!more&&items.length>0&&<p className="feed-loading">You’re all caught up for now.</p>}</>;
}
function SearchResults({q}){const[items,setItems]=useState([]),[loading,setLoading]=useState(false),[error,setError]=useState('');useEffect(()=>{let alive=true;const timer=setTimeout(async()=>{setLoading(true);const safe=q.trim().replace(/[%,()]/g,' ').slice(0,90);const {data,error:err}=await supabase.from('videos').select('id,title,summary,youtube_video_id,created_at,status').eq('status','approved').or(`title.ilike.%${safe}%,summary.ilike.%${safe}%`).order('created_at',{ascending:false}).limit(36);if(alive){setItems(data||[]);setError(err?.message||'');setLoading(false)}},250);return()=>{alive=false;clearTimeout(timer)}},[q]);return loading?<p className="muted">Searching videos…</p>:error?<p role="alert">{error}</p>:items.length?<VideoCards items={items}/>:<p className="muted">No matching videos found.</p>}
export default VideoGrid;
export {SearchResults};
