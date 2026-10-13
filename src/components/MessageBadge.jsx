import React,{useEffect,useState} from 'react';
import {supabase} from '../lib/supabase';
import {useAuth} from '../context/AuthContext';
export default function MessageBadge(){const {user}=useAuth();const[count,setCount]=useState(0);
useEffect(()=>{if(!user?.id)return;let active=true;
async function refresh(){const {count,error}=await supabase.from('messages').select('id',{count:'exact',head:true}).eq('receiver_id',user.id).is('read_at',null);if(active&&!error)setCount(count||0)}
refresh();const ch=supabase.channel('message-badge-'+user.id).on('postgres_changes',{event:'*',schema:'public',table:'messages'},refresh).subscribe();const timer=setInterval(refresh,10000);const onFocus=()=>refresh();window.addEventListener('focus',onFocus);window.addEventListener('farmday-messages-read',onFocus);return()=>{active=false;clearInterval(timer);window.removeEventListener('focus',onFocus);window.removeEventListener('farmday-messages-read',onFocus);supabase.removeChannel(ch)}},[user?.id]);
return count>0?<span className="message-count" aria-label={`${count} unread messages`}>{count>99?'99+':count}</span>:null;
}
