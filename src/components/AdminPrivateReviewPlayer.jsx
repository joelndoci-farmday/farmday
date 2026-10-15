import React,{useEffect,useState} from 'react';
import {supabase} from '../lib/supabase';
export default function AdminPrivateReviewPlayer({youtubeId,title}){
 const [url,setUrl]=useState(''),[error,setError]=useState('');
 useEffect(()=>{let active=true;setUrl('');setError('');
 (async()=>{
  if(!youtubeId)return;
  const {data:sessions,error:e}=await supabase.from('farmday_youtube_upload_sessions').select('id').eq('youtube_video_id',youtubeId).limit(1);
  if(e||!sessions?.length){if(active)setError('No private review copy linked to this video.');return;}
  const {data:preview,error:pe}=await supabase.from('farmday_review_previews').select('storage_path').eq('session_id',sessions[0].id).maybeSingle();
  if(pe||!preview){if(active)setError('This video was uploaded before private previews were enabled.');return;}
  const {data:signed,error:se}=await supabase.storage.from('farmday-admin-review').createSignedUrl(preview.storage_path,900);
  if(active){if(se)setError(se.message);else setUrl(signed.signedUrl)}
 })();return()=>{active=false}},[youtubeId]);
 return <div className="admin-private-player">{url?<video controls preload="metadata" playsInline src={url} style={{width:'100%',maxHeight:450,background:'#111',borderRadius:12}} aria-label={`Review ${title||'video'}`}/>:<p className="muted fine">{error||'Loading private video preview…'}</p>}</div>
}
