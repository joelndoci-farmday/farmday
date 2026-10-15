import React,{useEffect,useState} from 'react';
import {ExternalLink,Play,Upload} from 'lucide-react';
import {supabase} from '../lib/supabase';
import {uploadReviewAsset,frameFromVideo} from '../lib/adminReviewAssets';
const validId=id=>typeof id==='string'&&/^[A-Za-z0-9_-]{11}$/.test(id);
const sizes=['maxresdefault','sddefault','hqdefault','mqdefault','default'];
export default function AdminVideoPreview({youtubeId,title,uploadId,compact=false,publicVideo=false}){
 const [assets,setAssets]=useState(null),[videoUrl,setVideoUrl]=useState(''),[coverUrl,setCoverUrl]=useState(''),[thumbIndex,setThumbIndex]=useState(0),[thumbFailed,setThumbFailed]=useState(false),[open,setOpen]=useState(false),[busy,setBusy]=useState(false),[progress,setProgress]=useState(0),[message,setMessage]=useState('');
 const valid=validId(youtubeId);
 useEffect(()=>{let active=true;setAssets(null);setVideoUrl('');setCoverUrl('');setThumbIndex(0);setThumbFailed(false);setOpen(false);
 (async()=>{let asset=null;if(uploadId){const {data}=await supabase.from('farmday_admin_review_assets').select('video_path,cover_path').eq('upload_id',uploadId).maybeSingle();asset=data||null;}
 if(!asset?.video_path&&valid){const {data:sessions}=await supabase.from('farmday_youtube_upload_sessions').select('id').eq('youtube_video_id',youtubeId).limit(1);if(sessions?.length){const {data:copy}=await supabase.from('farmday_review_previews').select('storage_path').eq('session_id',sessions[0].id).maybeSingle();if(copy?.storage_path)asset={...asset,video_path:copy.storage_path};}}
 if(!active)return;setAssets(asset);
 if(asset?.cover_path){const {data}=await supabase.storage.from('farmday-admin-review').createSignedUrl(asset.cover_path,3600);if(active)setCoverUrl(data?.signedUrl||'');}
 if(asset?.video_path){const {data}=await supabase.storage.from('farmday-admin-review').createSignedUrl(asset.video_path,3600);if(active)setVideoUrl(data?.signedUrl||'');}
 })();return()=>{active=false};},[youtubeId,uploadId]);
 const youtubeUrl=valid?`https://www.youtube.com/watch?v=${youtubeId}`:null;
 const studioUrl=valid?`https://studio.youtube.com/video/${youtubeId}/edit`:null;
 const link=publicVideo?youtubeUrl:studioUrl;
 async function attach(file){if(!file||!uploadId)return;setBusy(true);setProgress(0);setMessage('');try{
 if(file.size>1024*1024*1024)throw new Error('Maximum 1 GB');
 const base=`admin-review/${uploadId}/${Date.now()}`;const videoPath=`${base}/${file.name.replace(/[^\w.-]/g,'_')}`;
 const frame=await frameFromVideo(file);
 await uploadReviewAsset(file,videoPath,setProgress);
 const coverPath=`${base}/cover.jpg`;const {error:ce}=await supabase.storage.from('farmday-admin-review').upload(coverPath,frame,{contentType:'image/jpeg',upsert:false});if(ce)throw ce;
 const {error}=await supabase.from('farmday_admin_review_assets').upsert({upload_id:uploadId,video_path:videoPath,cover_path:coverPath,updated_at:new Date().toISOString()},{onConflict:'upload_id'});if(error)throw error;
 const [video,cover]=await Promise.all([supabase.storage.from('farmday-admin-review').createSignedUrl(videoPath,3600),supabase.storage.from('farmday-admin-review').createSignedUrl(coverPath,3600)]);
 setAssets({video_path:videoPath,cover_path:coverPath});setVideoUrl(video.data?.signedUrl||'');setCoverUrl(cover.data?.signedUrl||'');setOpen(true);setMessage('Video and cover saved privately for Admin.');
 }catch(e){setMessage(`Could not save video: ${e.message}`)}finally{setBusy(false)}}
 const image=coverUrl?<img src={coverUrl} alt={`Cover: ${title||'video'}`}/>:valid&&!thumbFailed?<img src={`https://i.ytimg.com/vi/${youtubeId}/${sizes[thumbIndex]}.jpg`} alt={`Cover: ${title||'video'}`} onError={()=>thumbIndex<sizes.length-1?setThumbIndex(i=>i+1):setThumbFailed(true)}/>:null;
 const canPlayHere=Boolean(valid||videoUrl);
 return <div className={'admin-video-preview'+(compact?' compact':'')}>
 {open&&canPlayHere?<div className="farmday-admin-player">{valid?<iframe src={`https://www.youtube-nocookie.com/embed/${youtubeId}?autoplay=1&rel=0`} title={title||'YouTube video'} allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerPolicy="strict-origin-when-cross-origin" allowFullScreen/>:<video autoPlay controls playsInline preload="metadata" src={videoUrl}/>}<button type="button" className="btn outline" onClick={()=>setOpen(false)}>Close player</button></div>:
 <button type="button" className="admin-video-thumb" onClick={()=>canPlayHere&&setOpen(true)} disabled={!canPlayHere} title={canPlayHere?'Play inside FarmDay Admin':'Private YouTube video cannot be embedded'}>{image||<span className="admin-video-placeholder"><Play size={23}/><small>{publicVideo?'Cover unavailable':'Private cover unavailable'}</small></span>}<span className="admin-video-play"><Play size={19} fill="currentColor"/></span></button>}
 {!canPlayHere&&<small className="muted">Private on YouTube: playback in FarmDay requires the original private review copy. A YouTube private video cannot be embedded through an admin login.</small>}
 {publicVideo&&youtubeUrl&&<a href={youtubeUrl} target="_blank" rel="noopener noreferrer" className="admin-studio-link"><ExternalLink size={13}/> Public video on YouTube</a>}
 {!publicVideo&&studioUrl&&<a href={studioUrl} target="_blank" rel="noopener noreferrer" className="admin-studio-link"><ExternalLink size={13}/> Open video in YouTube Studio</a>}

 {message&&<small role="status" className="muted">{message}</small>}
 </div>;
}
