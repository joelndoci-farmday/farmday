import React,{useCallback,useEffect,useState} from 'react';
import {supabase} from '../lib/supabase';

/** Only show green when Google confirms the authorized channel and write scope. */
export default function YouTubeConnection({compact=false}){
 const [status,setStatus]=useState(null);
 const [busy,setBusy]=useState(false);
 const [message,setMessage]=useState('');
 const refresh=useCallback(async()=>{
  try{
   const {data,error}=await supabase.functions.invoke('farmday-youtube-admin-actions',{body:{action:'connection_health'}});
   if(error)throw error;
   setStatus(data);
   setMessage('');
  }catch(e){setStatus({connected:false,reconnect_required:true});setMessage('Could not verify the YouTube connection. '+(e?.message||''));}
 },[]);
 useEffect(()=>{
  refresh();
  const timer=window.setInterval(refresh,120000);
  const onFocus=()=>refresh();
  window.addEventListener('focus',onFocus);
  return ()=>{window.clearInterval(timer);window.removeEventListener('focus',onFocus)};
 },[refresh]);
 async function connect(){
  setBusy(true);setMessage('');
  try{
   const {data,error}=await supabase.functions.invoke('youtube-oauth-start',{body:{}});
   if(error)throw error;
   const url=data?.authorization_url;
   if(!url||!url.startsWith('https://accounts.google.com/'))throw new Error('Google authorization URL is missing');
   window.location.assign(url);
  }catch(e){setMessage(e?.message||'Connection failed');setBusy(false)}
 }
 const verified=!!status?.connected&&!!status?.can_manage;
 return <section className={'farmday-youtube-health'+(compact?' farmday-youtube-health-compact':'')} aria-live="polite">
  <div className="farmday-youtube-health-main">
   <span aria-hidden="true" className={'farmday-youtube-health-indicator '+(verified?'verified':'needs-attention')}>{verified?'✓':'!'}</span>
   <div><strong>{status===null?'Checking YouTube connection…':verified?'YouTube connection secure':status?.connected?'YouTube reconnection required':'YouTube connection needs attention'}</strong>
    <div className="muted fine">{verified?(status.channel_title||'FarmDay')+' · automatic authorization renewal enabled':status?.reason||'Checking channel permissions and Google authorization'}</div>
   </div>
  </div>
  <div className="rowactions">
   {!verified&&status!==null&&<button className="btn primary" type="button" disabled={busy} onClick={connect}>{busy?'Opening Google…':'Reconnect YouTube once'}</button>}
   <button className="btn outline" type="button" onClick={refresh} disabled={busy}>Check connection</button>
  </div>
  {message&&<p className="muted fine" role="alert">{message}</p>}
 </section>;
}
