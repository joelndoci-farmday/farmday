import React,{useState,useEffect,createContext,useContext} from 'react';
import{BrowserRouter,Routes,Route,Link,NavLink,Navigate,useParams}from'react-router-dom';
import{Sprout,Search,Menu,X,Play,Upload,User,LogOut,ShieldCheck,MessageCircle,Send,CheckCircle2,Clock,Video,ArrowRight,Globe,Leaf,Heart,ExternalLink,Lock,Plus,Settings}from'lucide-react';
import {useAuth} from '../context/AuthContext';
function Protected({children,admin=false}){const{user,profile,loading}=useAuth();if(loading)return <main className="wrap space">Verifying your account…</main>;if(!user)return <Navigate to="/auth" replace/>;if(admin&&!profile?.is_admin)return <Navigate to="/" replace/>;return children}
const yt=id=>`https://www.youtube.com/watch?v=${id}`;function getYtId(s){try{const u=new URL(s);if(u.hostname.includes('youtu.be'))return u.pathname.slice(1).split('/')[0];if(u.hostname.includes('youtube.com')){if(u.pathname.startsWith('/shorts/'))return u.pathname.split('/')[2];return u.searchParams.get('v')}}catch{}return null}

export default Protected;
