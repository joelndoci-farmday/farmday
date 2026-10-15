import {useEffect} from 'react';
import {useAuth} from '../context/AuthContext';
import {supabase} from '../lib/supabase';
import {REGISTRATION_TERMS_VERSION} from '../lib/registrationTerms';
export default function RegistrationAcceptanceSync(){
 const {user}=useAuth();
 useEffect(()=>{
  if(!user || (sessionStorage.getItem('farmday_google_registration_terms')!==REGISTRATION_TERMS_VERSION && user.user_metadata?.registration_terms_version!==REGISTRATION_TERMS_VERSION))return;
  let cancelled=false;
  (async()=>{
   const {data,error}=await supabase.from('user_agreements').select('id').eq('user_id',user.id).eq('terms_version',REGISTRATION_TERMS_VERSION).is('video_id',null).limit(1);
   if(error||cancelled)return;
   if(!data?.length){const result=await supabase.from('user_agreements').insert({user_id:user.id,video_id:null,terms_version:REGISTRATION_TERMS_VERSION});if(result.error)return;}
   if(!cancelled)sessionStorage.removeItem('farmday_google_registration_terms');
  })();return()=>{cancelled=true};
 },[user?.id]);return null;
}
