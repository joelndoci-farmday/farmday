import {supabase} from './supabase';
const BUCKET='farmday-admin-review';
const B64=s=>btoa(unescape(encodeURIComponent(s)));
/** Resumable upload using the TUS protocol; videos stay in a private bucket. */
export async function savePrivateReviewCopy(file,userId,sessionId,onProgress=()=>{}){
 const {data:{session}}=await supabase.auth.getSession();
 if(!session?.access_token)throw new Error('Session expired.');
 const objectName=`${userId}/${sessionId}/${file.name.replace(/[^a-zA-Z0-9._-]/g,'_')}`;
 const url=`${import.meta.env.VITE_SUPABASE_URL}/storage/v1/upload/resumable`;
 const headers={'Authorization':`Bearer ${session.access_token}`,'apikey':import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY,'Tus-Resumable':'1.0.0'};
 const create=await fetch(url,{method:'POST',headers:{...headers,'Upload-Length':String(file.size),'Upload-Metadata':`bucketName ${B64(BUCKET)},objectName ${B64(objectName)},contentType ${B64(file.type||'video/mp4')},cacheControl ${B64('3600')}`,'x-upsert':'false'}});
 if(!create.ok)throw new Error(`Private preview initialization failed (${create.status}): ${await create.text()}`);
 const location=create.headers.get('Location');
 if(!location)throw new Error('Private preview upload location missing.');
 const uploadUrl=new URL(location,url).toString();
 let offset=0;
 while(offset<file.size){
  const chunk=file.slice(offset,Math.min(file.size,offset+6*1024*1024));
  const response=await fetch(uploadUrl,{method:'PATCH',headers:{...headers,'Content-Type':'application/offset+octet-stream','Upload-Offset':String(offset)},body:chunk});
  if(!response.ok)throw new Error(`Private preview transfer failed (${response.status}): ${await response.text()}`);
  const next=Number(response.headers.get('Upload-Offset'));
  offset=Number.isFinite(next)&&next>offset?next:offset+chunk.size;
  onProgress(Math.round(offset/file.size*100));
 }
 const {error}=await supabase.from('farmday_review_previews').insert({session_id:sessionId,user_id:userId,storage_path:objectName});
 if(error)throw error;
 return objectName;
}
