import {supabase} from './supabase';
const bucket='farmday-admin-review';
const b64=s=>btoa(unescape(encodeURIComponent(s)));
export async function uploadReviewAsset(file,path,onProgress=()=>{}){
 const {data:{session}}=await supabase.auth.getSession();
 if(!session?.access_token)throw new Error('Please sign in again.');
 const base=import.meta.env.VITE_SUPABASE_URL;
 const key=import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY||import.meta.env.VITE_SUPABASE_ANON_KEY;
 const headers={Authorization:`Bearer ${session.access_token}`,apikey:key,'Tus-Resumable':'1.0.0'};
 const init=await fetch(`${base}/storage/v1/upload/resumable`,{method:'POST',headers:{...headers,'Upload-Length':String(file.size),'Upload-Metadata':`bucketName ${b64(bucket)},objectName ${b64(path)},contentType ${b64(file.type||'video/mp4')},cacheControl ${b64('3600')}`},});
 if(!init.ok)throw new Error(`Upload failed (${init.status}): ${await init.text()}`);
 const location=init.headers.get('Location');if(!location)throw new Error('Upload URL missing');
 const url=new URL(location,base).toString();let offset=0;
 while(offset<file.size){const chunk=file.slice(offset,offset+6*1024*1024);const r=await fetch(url,{method:'PATCH',headers:{...headers,'Content-Type':'application/offset+octet-stream','Upload-Offset':String(offset)},body:chunk});if(!r.ok)throw new Error(`Upload interrupted (${r.status}): ${await r.text()}`);const next=Number(r.headers.get('Upload-Offset'));offset=Number.isFinite(next)&&next>offset?next:offset+chunk.size;onProgress(Math.round(100*offset/file.size));}
 return path;
}
export async function frameFromVideo(file){
 const src=URL.createObjectURL(file);const v=document.createElement('video');v.muted=true;v.preload='auto';v.playsInline=true;v.src=src;
 try{await new Promise((resolve,reject)=>{v.onloadedmetadata=resolve;v.onerror=()=>reject(new Error('Could not read video for thumbnail'));});
 const seek=Math.min(1,Math.max(0,v.duration/4||0));
 if(seek>0)await new Promise((resolve,reject)=>{v.onseeked=resolve;v.onerror=()=>reject(new Error('Could not capture frame'));v.currentTime=seek;});
 const canvas=document.createElement('canvas');const ratio=Math.min(1,640/(v.videoWidth||640));canvas.width=Math.round((v.videoWidth||640)*ratio);canvas.height=Math.round((v.videoHeight||360)*ratio);canvas.getContext('2d').drawImage(v,0,0,canvas.width,canvas.height);
 const blob=await new Promise(resolve=>canvas.toBlob(resolve,'image/jpeg',.82));if(!blob)throw new Error('Thumbnail capture failed');return blob;
 }finally{v.removeAttribute('src');v.load();URL.revokeObjectURL(src)}
}
