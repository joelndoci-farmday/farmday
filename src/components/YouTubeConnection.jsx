import React,{useEffect,useState} from 'react';
import {supabase} from '../lib/supabase';
export default function YouTubeConnection(){
 const [status,setStatus]=useState(null),[busy,setBusy]=useState(false),[message,setMessage]=useState('');
 async function refresh(){const {data,error}=await supabase.rpc('farmday_youtube_connection_status');if(error)setMessage(error.message);else setStatus(data)}
 useEffect(()=>{refresh()},[]);
 async function connect(){setBusy(true);setMessage('');try{
 const {data,error}=await supabase.functions.invoke('youtube-oauth-start',{body:{}});
 if(error)throw error;
 const url=data?.url||data?.auth_url||data?.authorization_url;
 if(!url||!url.startsWith('https://accounts.google.com/'))throw new Error('OAuth start did not return a recognized Google authorization URL. Check the Edge Function response.');
 window.location.assign(url);
 }catch(e){setMessage(e.message||'Connection failed');setBusy(false)}}
 return <section className="safety-section"><h2>YouTube channel connection</h2><p className="muted">Only the Farmday administrator may authorize the channel. OAuth tokens remain server-side. Connecting does not publish videos.</p>{status?.connected?<p className="notice">Connected: <strong>{status.channel_title||status.channel_id||'YouTube channel'}</strong> · <button className="text-button" onClick={refresh}>Refresh</button></p>:<div className="rowactions"><button className="btn primary" disabled={busy} onClick={connect}>{busy?'Opening Google…':'Connect Farmday YouTube'}</button><button className="btn outline" onClick={refresh}>Check status</button></div>}{message&&<p className="notice" role="alert">{message}</p>}<p className="muted fine">Direct large-file upload is not enabled yet: it requires a secure resumable upload gateway and verified YouTube API permissions. Never place OAuth tokens in the browser.</p></section>
}
