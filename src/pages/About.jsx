import React,{useState,useEffect,createContext,useContext} from 'react';
import{BrowserRouter,Routes,Route,Link,NavLink,Navigate,useParams}from'react-router-dom';
import{Sprout,Search,Menu,X,Play,Upload,User,LogOut,ShieldCheck,MessageCircle,Send,CheckCircle2,Clock,Video,ArrowRight,Globe,Leaf,Heart,ExternalLink,Lock,Plus,Settings}from'lucide-react';

function About(){return <main className="wrap section narrow"><span className="kicker">OUR MISSION</span><h1 className="pageTitle">A world growing together.</h1><p className="lead">Farmday is a community for farmers, creators and everyone passionate about agriculture. A place to share knowledge, experience and real stories.</p><p>Submitted videos are reviewed before appearing. Farmday shares videos on its social channels only with the appropriate rights and permissions.</p><Link className="btn primary" to="/auth">Join us <ArrowRight size={18}/></Link></main>}

export default About;
