import React,{useEffect,useState} from 'react';
import {MessageCircle,X} from 'lucide-react';
import {useLocation} from 'react-router-dom';
import {useAuth} from '../context/AuthContext';
import MessageBadge from './MessageBadge';
import Messages from '../pages/Messages';
export default function FloatingMessages(){const {user}=useAuth();const [open,setOpen]=useState(false);const location=useLocation();useEffect(()=>{if(location.pathname==='/messages'||location.search.includes('to='))setOpen(true)},[location.pathname,location.search]);if(!user)return null;return <div className={'farmday-chat-widget '+(open?'is-open':'')}>{<section style={{display:open?'flex':'none'}} className="farmday-chat-panel" role="dialog" aria-label="Farmday messages"><div className="farmday-chat-header"><span><MessageCircle size={18}/> Messages</span><button aria-label="Close messages" onClick={()=>setOpen(false)}><X size={20}/></button></div><Messages embedded/></section>}<button type="button" className="farmday-chat-launcher" onClick={()=>setOpen(o=>!o)} aria-label={open?'Close messages':'Open messages'} aria-expanded={open}><MessageCircle size={24}/><span>Messages</span><MessageBadge/></button></div>}
