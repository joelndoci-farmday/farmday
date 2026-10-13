import React,{useState,useEffect,createContext,useContext} from 'react';
import {supabase} from '../lib/supabase';
const C=createContext(null);export const useAuth=()=>useContext(C);
function Provider({children}){const[user,setUser]=useState(null),[profile,setProfile]=useState(null),[loading,setLoading]=useState(true);async function refresh(){const{data:{user:u}}=await supabase.auth.getUser();setUser(u);if(u){const{data}=await supabase.from('profiles').select('*').eq('id',u.id).maybeSingle();setProfile(data)}else setProfile(null);setLoading(false)}useEffect(()=>{refresh();const{data:{subscription}}=supabase.auth.onAuthStateChange(()=>{setTimeout(refresh,0)});return()=>subscription.unsubscribe()},[]);return <C.Provider value={{user,profile,loading,refresh,supabase}}>{children}</C.Provider>}

export default Provider;
