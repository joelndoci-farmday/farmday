import React,{useEffect,useState} from 'react';
import {Link,useParams} from 'react-router-dom';
import {ExternalLink,Play} from 'lucide-react';
import {supabase} from '../lib/supabase';
import {recordWatch,relatedVideos} from '../lib/recommendations';
import {yt} from '../lib/youtube';

const valid=id=>/^[A-Za-z0-9_-]{11}$/.test(id||'');
export default function WatchPage(){
 const {id}=useParams();
 const [video,setVideo]=useState(null),[pool,setPool]=useState([]),[loading,setLoading]=useState(true),[started,setStarted]=useState(false);
 useEffect(()=>{let active=true;setLoading(true);setVideo(null);setStarted(false);
 (async()=>{
  if(!valid(id)){if(active)setLoading(false);return}
  const [approved,catalog,others]=await Promise.all([
   supabase.from('videos').select('id,title,summary,youtube_video_id,status').eq('youtube_video_id',id).eq('status','approved').maybeSingle(),
   supabase.from('farmday_public_youtube_catalog').select('upload_id,title,description,youtube_video_id,thumbnail_url').eq('youtube_video_id',id).maybeSingle(),
   Promise.all([
    supabase.from('videos').select('id,title,summary,youtube_video_id').eq('status','approved').order('created_at',{ascending:false}).limit(100),
    supabase.from('farmday_public_youtube_catalog').select('upload_id,title,description,youtube_video_id,thumbnail_url').order('checked_at',{ascending:false}).limit(100)
   ])
  ]);
  if(!active)return;
  const selected=approved.data||catalog.data;
  const all=[...(others[0].data||[]),...(others[1].data||[])];
  const ids=new Set();setPool(all.filter(x=>{if(ids.has(x.youtube_video_id))return false;ids.add(x.youtube_video_id);return true}));
  setVideo(selected||null);setLoading(false);
 })();return()=>{active=false}},[id]);
 const suggestions=relatedVideos(pool,video,8);
 return <main className="wrap section">{loading?<p>Loading video…</p>:!video?<p>Video unavailable or not approved.</p>:<div className="watch"><div>
 <div className="embed">{!started?<button type="button" className="farmday-start-video" onClick={()=>{recordWatch(video);setStarted(true)}} aria-label="Play video on Farmday"><img src={video.thumbnail_url||`https://i.ytimg.com/vi/${id}/hqdefault.jpg`} alt=""/><span><Play size={32} fill="currentColor"/> Play on Farmday</span></button>:<iframe key={id} src={`https://www.youtube-nocookie.com/embed/${id}?rel=0&playsinline=1&autoplay=1`} title={video.title||'Farmday video'} allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture; web-share" referrerPolicy="strict-origin-when-cross-origin" allowFullScreen/>}</div>
 <h1>{video.title}</h1><p className="muted">{video.summary||video.description}</p>
 <div className="video-actions"><a className="btn outline" href={yt(id)} target="_blank" rel="noopener noreferrer"><ExternalLink size={16}/> Watch on YouTube</a>{video.id&&<Link className="btn outline" to={'/video/'+video.id}>Comments & Likes</Link>}</div>
 <p className="muted">Videos play here on Farmday using YouTube's official embedded player.</p>
 </div><aside className="aside"><h3>More videos like this</h3>{suggestions.map(v=><Link key={v.youtube_video_id} className="farmday-related-video" to={'/watch/'+v.youtube_video_id}><img loading="lazy" src={v.thumbnail_url||`https://i.ytimg.com/vi/${v.youtube_video_id}/mqdefault.jpg`} alt=""/><span><Play size={14}/>{v.title}</span></Link>)}</aside></div>}</main>
}
