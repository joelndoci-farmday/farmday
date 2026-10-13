import React,{useCallback,useEffect,useState} from 'react';
import {Link} from 'react-router-dom';
import {Play,Heart,MessageCircle} from 'lucide-react';
import {supabase} from '../lib/supabase';
import {useAuth} from '../context/AuthContext';
const PAGE=8;
export default function FarmerVideos({farmerId}){
 const {user}=useAuth();const [videos,setVideos]=useState([]),[page,setPage]=useState(0),[more,setMore]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const load=useCallback(async(reset=false)=>{
  if(!farmerId)return;setBusy(true);setError('');const index=reset?0:page;
  const {data,error:err}=await supabase.from('videos').select('id,title,summary,youtube_video_id,created_at').eq('uploaded_by',farmerId).eq('status','approved').order('created_at',{ascending:false}).range(index*PAGE,index*PAGE+PAGE-1);
  if(err){setError(err.message);setBusy(false);return;}
  const ids=(data||[]).map(v=>v.id);let likes=[],comments=[];
  if(ids.length){const a=await Promise.all([supabase.from('video_likes').select('video_id,user_id').in('video_id',ids),supabase.from('comments').select('video_id').in('video_id',ids)]);likes=a[0].data||[];comments=a[1].data||[];}
  const enriched=(data||[]).map(v=>({...v,likes:likes.filter(l=>l.video_id===v.id).length,liked:likes.some(l=>l.video_id===v.id&&l.user_id===user?.id),comments:comments.filter(c=>c.video_id===v.id).length}));
  setVideos(prev=>reset?enriched:[...prev,...enriched.filter(v=>!prev.some(p=>p.id===v.id))]);setMore((data||[]).length===PAGE);setPage(index+1);setBusy(false);
 },[farmerId,page,user?.id]);
 useEffect(()=>{setVideos([]);setPage(0);let alive=true;(async()=>{if(!farmerId)return;const {data,error:err}=await supabase.from('videos').select('id,title,summary,youtube_video_id,created_at').eq('uploaded_by',farmerId).eq('status','approved').order('created_at',{ascending:false}).range(0,PAGE-1);if(!alive)return;if(err){setError(err.message);return;}const ids=(data||[]).map(v=>v.id);const results=ids.length?await Promise.all([supabase.from('video_likes').select('video_id,user_id').in('video_id',ids),supabase.from('comments').select('video_id').in('video_id',ids)]):[];if(!alive)return;const likes=results[0]?.data||[],comments=results[1]?.data||[];setVideos((data||[]).map(v=>({...v,likes:likes.filter(l=>l.video_id===v.id).length,liked:likes.some(l=>l.video_id===v.id&&l.user_id===user?.id),comments:comments.filter(c=>c.video_id===v.id).length})));setMore((data||[]).length===PAGE);setPage(1)})();return()=>{alive=false}},[farmerId,user?.id]);
 async function toggle(v){if(!user)return;const result=v.liked?await supabase.from('video_likes').delete().eq('video_id',v.id).eq('user_id',user.id):await supabase.from('video_likes').insert({video_id:v.id,user_id:user.id});if(result.error)return setError(result.error.message);setVideos(prev=>prev.map(x=>x.id===v.id?{...x,liked:!x.liked,likes:x.likes+(x.liked?-1:1)}:x))}
 return <div className="farmer-video-feed">{videos.map(v=><article className="farmer-feed-item" key={v.id}><Link to={'/video/'+v.id} className="farmer-video-thumb"><img loading="lazy" src={'https://img.youtube.com/vi/'+encodeURIComponent(v.youtube_video_id)+'/hqdefault.jpg'} alt={v.title}/><span className="play"><Play fill="currentColor"/></span></Link><h3><Link to={'/video/'+v.id}>{v.title}</Link></h3>{v.summary&&<p className="muted">{v.summary}</p>}<div className="rowactions">{user?<button className={'btn outline '+(v.liked?'liked':'')} onClick={()=>toggle(v)}><Heart size={17} fill={v.liked?'currentColor':'none'}/> {v.likes} {v.liked?'Unlike':'Like'}</button>:<Link className="btn outline" to="/auth"><Heart size={17}/> {v.likes} Likes</Link>}<Link className="btn outline" to={'/video/'+v.id}><MessageCircle size={17}/> {v.comments} Comments</Link></div></article>)}{!busy&&!videos.length&&!error&&<p className="muted">No published videos yet. Videos under review are not public.</p>}{error&&<p role="alert">{error}</p>}{more&&<button className="btn outline" disabled={busy} onClick={()=>load(false)}>{busy?'Loading...':'Load more videos'}</button>}</div>
}
