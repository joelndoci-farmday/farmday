import React,{useState} from 'react';
import {useNavigate} from 'react-router-dom';
import {ArrowRight,UploadCloud,X} from 'lucide-react';
import {supabase} from '../lib/supabase';
import {useAuth} from '../context/AuthContext';
import {TERMS_VERSION} from '../lib/uploadTerms';
import {analyzeOriginalFile} from '../lib/mediaFingerprint';
import {savePrivateReviewCopy} from '../lib/privateReviewUpload';
const MAX=1024*1024*1024;
const CHUNK=2*1024*1024;
export default function UploadPage(){
 const {user}=useAuth(),navigate=useNavigate();
 const [analysisMessage,setAnalysisMessage]=useState('');const [progress,setProgress]=useState(0);const [open,setOpen]=useState(true),[stage,setStage]=useState('details'),[file,setFile]=useState(null),[title,setTitle]=useState(''),[description,setDescription]=useState(''),[busy,setBusy]=useState(false),[message,setMessage]=useState('');
 function close(){if(busy)return;setOpen(false);navigate('/');}
 async function submit(e){
 e.preventDefault();setMessage('');
 if(!file||!user)return setMessage('Please sign in and choose a video.');
 if(file.size>MAX)return setMessage('Maximum 1 GB per video.');
 if(!['video/mp4','video/quicktime','video/webm','video/x-m4v'].includes(file.type))return setMessage('Choose an MP4, MOV, WebM or M4V video.');
 if(title.trim().length<5)return setMessage('Please enter a title of at least 5 characters.');
 setBusy(true);setStage('uploading');setProgress(0);
 try{
  let signals=null;
  try{signals=await analyzeOriginalFile(file,setAnalysisMessage)}catch(err){setAnalysisMessage('Preliminary fingerprint unavailable: '+err.message)}
  const requestAnalysis=async()=>{try{const {data}=await supabase.functions.invoke('farmday-media-kick',{body:{session_id:startSessionId}});if(data?.immediate)setAnalysisMessage('Server analysis requested.');else setAnalysisMessage('Server analysis is unavailable without a temporary transfer endpoint; manual review required.')}catch{setAnalysisMessage('Upload complete; server analysis will be retried by the scheduled worker.')}};
  let startSessionId='';
  const saveSignals=async(uploadId)=>{if(!signals?.sha256||!uploadId)return;const {error}=await supabase.rpc('farmday_submit_client_fingerprints',{p_upload_id:uploadId,p_sha256:signals.sha256,p_visual:signals.visual||'',p_audio:signals.audio||''});setAnalysisMessage(error?'Fingerprint storage pending: '+error.message:'Preliminary fingerprint recorded. Rights and monetization remain unverified.')};
  const {data:start,error:startError}=await supabase.functions.invoke('farmday-youtube-upload',{body:{action:'start',title:title.trim(),description:description.trim(),mime_type:file.type,total_bytes:file.size,terms_version:TERMS_VERSION}});
  if(startError||!start?.session_id)throw new Error(start?.error||startError?.message||'Could not start video upload.');
  startSessionId=start.session_id;
  // Temporary private original: the server worker deletes it after successful analysis.
  // Never send the video to YouTube if the required review copy failed.
  await savePrivateReviewCopy(file,user.id,start.session_id);
  setAnalysisMessage('Private analysis copy ready. Server FFmpeg/Chromaprint analysis queued.');
  const {data:{session}}=await supabase.auth.getSession();
  if(!session?.access_token)throw new Error('Please sign in again.');
  let offset=0;
  while(offset<file.size){
   const chunk=file.slice(offset,Math.min(offset+CHUNK,file.size));
   let succeeded=false;
   for(let attempt=0;attempt<3&&!succeeded;attempt++){
    try{
     const response=await fetch(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/farmday-youtube-upload`,{method:'PUT',headers:{'Authorization':`Bearer ${session.access_token}`,'apikey':import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY,'Content-Type':'application/octet-stream','x-upload-id':start.session_id,'x-upload-offset':String(offset)},body:chunk});
     const result=await response.json();
     if(!response.ok){if(response.status===409&&Number.isFinite(result.offset_bytes)){offset=result.offset_bytes;succeeded=true;break;}throw new Error(result.error||`Transfer failed (${response.status})`);}
     offset=result.offset_bytes;
     setProgress(Math.min(100,Math.round(offset/file.size*100)));
     if(result.completed){await saveSignals(result.upload_id);await requestAnalysis();setStage('done');return;}
     succeeded=true;
    }catch(error){
     if(attempt===2)throw error;
     const {data:state,error:statusError}=await supabase.functions.invoke('farmday-youtube-upload',{body:{action:'status',session_id:start.session_id}});
     if(!statusError&&state?.state==='completed'){await requestAnalysis();setStage('done');return;}
     if(!statusError&&Number.isFinite(state?.offset_bytes)){offset=state.offset_bytes;succeeded=true;}
    }
   }
  }
  setStage('done');
 }catch(err){setStage('details');setMessage(err.message||'Upload failed. Please try again.');}
 finally{setBusy(false);}
 }
 return <main className="wrap section"><div className="upload-landing"><h1>Upload Video</h1><p className="muted">Share your farming story with the Farmday community.</p></div>{open&&<div className="upload-overlay" role="presentation"><section className="upload-dialog" role="dialog" aria-modal="true" aria-label="Upload video"><button className="upload-close" type="button" onClick={close} disabled={busy} aria-label="Close"><X size={20}/></button>
 {stage==='done'?<div className="upload-result"><UploadCloud size={42}/><h2>Video submitted successfully!</h2><p>Your video is being reviewed by Farmday. Review may take up to 24 hours, but this is an estimate, not a guarantee. You can leave this page now.</p><button className="btn primary" onClick={close}>Done</button></div>:
 stage==='uploading'?<div className="upload-result"><UploadCloud size={42}/><h2>Uploading your video… {progress}%</h2><progress max="100" value={progress} style={{width:'100%'}}/><p>Please keep this page open until the upload is complete. Do not close the browser yet.</p></div>:
 <form className="form" onSubmit={submit}><h2>Choose your video</h2><label className="file-select"><UploadCloud size={25}/><span>{file?file.name:'Choose video from your phone gallery or computer folder'}</span><input type="file" accept="video/mp4,video/quicktime,video/webm,video/x-m4v,video/*" required onChange={e=>setFile(e.target.files?.[0]||null)}/></label><p className="muted fine">MP4, MOV, WebM or M4V · Maximum 1 GB</p><label>Video title<input required minLength={5} maxLength={180} value={title} onChange={e=>setTitle(e.target.value)}/></label><label>Description (optional)<textarea maxLength={2000} rows={3} value={description} onChange={e=>setDescription(e.target.value)}/></label><div className="rowactions"><button className="btn primary" type="submit" disabled={busy||!file}>Done — Submit for review</button></div><p className="muted fine">Your video will be reviewed before publication.</p></form>}
 {message&&<p role="alert" className="notice">{message}</p>}</section></div>}</main>
}
