import React from 'react';
import {UserRound} from 'lucide-react';
export default function Avatar({profile,size=44}){return profile?.avatar_url?<img className="fd-avatar" src={profile.avatar_url} alt={`${profile.user_name||'Farmer'} profile`} style={{width:size,height:size}}/>:<span className="fd-avatar fd-avatar-empty" style={{width:size,height:size}}><UserRound size={size*.55}/></span>}
