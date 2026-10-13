import React,{useEffect,useState} from 'react';
import {Link,useSearchParams} from 'react-router-dom';
import {Search,MapPin,UserRound,MessageCircle,ArrowRight} from 'lucide-react';
import {supabase} from '../lib/supabase';
import {useAuth} from '../context/AuthContext';
import Avatar from '../components/Avatar';
import VideoGrid,{SearchResults} from '../components/VideoGrid';

function Farmers({query}){
 const {user}=useAuth();const [farmers,setFarmers]=useState([]),[loading,setLoading]=useState(true),[error,setError]=useState('');
 useEffect(()=>{let alive=true;setLoading(true);const timer=setTimeout(async()=>{
  const safe=query.trim().replace(/[%,()]/g,' ').slice(0,90);
  let req=supabase.from('profiles').select('id,user_name,farm_name,location,bio,avatar_url').order('created_at',{ascending:false}).limit(36);
  if(safe)req=req.or(`user_name.ilike.%${safe}%,farm_name.ilike.%${safe}%,location.ilike.%${safe}%`);
  const {data,error}=await req;if(alive){setFarmers(data||[]);setError(error?.message||'');setLoading(false)}
 },250);return()=>{alive=false;clearTimeout(timer)}},[query]);
 return <section className="farmer-results"><div className="sectionTop"><h2>Farmers & farms</h2><span className="muted">{farmers.length} profiles</span></div>{loading?<p className="muted">Searching farmers…</p>:error?<p role="alert">{error}</p>:farmers.length===0?<p className="muted">No farmers found. Try a name, farm or location.</p>:<div className="farmer-grid">{farmers.map(f=><article className="farmer-card" key={f.id}><Link className="farmer-identity" to={'/farmer/'+encodeURIComponent(f.user_name)}><Avatar profile={f} size={58}/><span><strong>{f.farm_name||f.user_name}</strong><small>@{f.user_name}</small></span></Link>{f.location&&<p className="muted farmer-location"><MapPin size={14}/>{f.location}</p>}{f.bio&&<p className="farmer-bio">{f.bio}</p>}<div className="rowactions"><Link className="btn primary" to={'/farmer/'+encodeURIComponent(f.user_name)}><UserRound size={15}/> View profile</Link>{user&&user.id!==f.id&&<Link className="btn outline" to={'/messages?to='+encodeURIComponent(f.user_name)}><MessageCircle size={15}/> Message</Link>}</div></article>)}</div>}</section>
}
export default function Videos(){const [params]=useSearchParams();const [q,setQ]=useState(params.get('q')||''),[tab,setTab]=useState('all');const query=q.trim();return <main className="wrap section"><span className="kicker">FARMDAY COMMUNITY</span><h1 className="pageTitle">Discover</h1><p className="muted">Discover farming stories and connect with farmers around the world.</p><div className="search"><Search size={20}/><input aria-label="Search videos, farmers and farms" value={q} onChange={e=>setQ(e.target.value)} placeholder="Search video titles, descriptions, farmers, farms or locations…"/></div><div className="explore-tabs" role="group" aria-label="Explore categories">{[['all','All'],['videos','Videos'],['farmers','Farmers & Farms']].map(([key,label])=><button type="button" key={key} className={tab===key?'active':''} onClick={()=>setTab(key)}>{label}</button>)}</div>{tab!=='videos'&&<Farmers query={query}/ >}{tab!=='farmers'&&<section className="explore-videos"><div className="sectionTop"><h2>Videos</h2>{query&&<span className="muted">Results for “{query}”</span>}</div>{query?<SearchResults q={query}/>:<VideoGrid/>}</section>}</main>}
