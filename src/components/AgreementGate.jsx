import React,{useEffect,useState} from 'react';
import {supabase} from '../lib/supabase';
import {useAuth} from '../context/AuthContext';
import AgreementModal from './AgreementModal';
import {REGISTRATION_TERMS_VERSION} from '../lib/registrationTerms';
export default function AgreementGate(){
 const {user,loading}=useAuth();const [status,setStatus]=useState('checking'),[busy,setBusy]=useState(false),[error,setError]=useState('');
 useEffect(()=>{let cancelled=false;setStatus('checking');setError('');if(!user){setStatus('none');return;}
 supabase.from('user_agreements').select('id').eq('user_id',user.id).eq('terms_version',REGISTRATION_TERMS_VERSION).is('video_id',null).limit(1).then(({data,error})=>{if(cancelled)return;if(error){setStatus('error');setError(error.message)}else setStatus(data?.length?'accepted':'required')});return()=>{cancelled=true}},[user?.id]);
 async function accept(){if(!user)return;setBusy(true);setError('');const {error}=await supabase.from('user_agreements').insert({user_id:user.id,terms_version:REGISTRATION_TERMS_VERSION,video_id:null});if(error){setError(error.message)}else{setStatus('accepted')}setBusy(false)}
 if(loading||!user||status==='accepted'||status==='none'||status==='checking')return null;
 return <><AgreementModal busy={busy} onAccept={accept} onDecline={()=>supabase.auth.signOut()}/>{error&&<div className="agreement-error" role="alert">Could not verify your agreement: {error}</div>}</>
}
