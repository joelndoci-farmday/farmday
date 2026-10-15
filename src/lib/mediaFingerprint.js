// Browser-side preliminary signals only. Never certify copyright or monetization.
const hex = bytes => Array.from(new Uint8Array(bytes), b=>b.toString(16).padStart(2,'0')).join('');
export async function analyzeOriginalFile(file, onProgress=()=>{}) {
  if (!crypto?.subtle) throw new Error('Secure browser context required for hashing.');
  // WebCrypto digest buffers its input; avoid exhausting phones on large uploads.
  if (file.size > 150*1024*1024) return {sha256:null, visual:null, note:'File exceeds 150 MB browser hashing safety limit. Cloud media worker required.'};
  onProgress('Computing exact-file SHA-256…');
  const sha256=hex(await crypto.subtle.digest('SHA-256',await file.arrayBuffer()));
  let visual=null;
  const url=URL.createObjectURL(file);
  const video=document.createElement('video');video.muted=true;video.preload='auto';video.playsInline=true;video.src=url;
  const wait=(name,ms=15000)=>new Promise((resolve,reject)=>{const timer=setTimeout(()=>{cleanup();reject(Error('Video decode timeout'))},ms);function cleanup(){clearTimeout(timer);video.removeEventListener(name,done);video.removeEventListener('error',fail)}function done(){cleanup();resolve()}function fail(){cleanup();reject(Error('Video decode failed'))}video.addEventListener(name,done,{once:true});video.addEventListener('error',fail,{once:true})});
  try {
    onProgress('Sampling visual frames…');
    await wait('loadedmetadata');
    const duration=Number(video.duration);
    if(!Number.isFinite(duration)||duration<=0)throw Error('Invalid video duration');
    const canvas=document.createElement('canvas');canvas.width=9;canvas.height=8;const ctx=canvas.getContext('2d',{willReadFrequently:true});
    const hashes=[];
    for(const second of [...new Set([duration*.1,duration*.35,duration*.6,duration*.85].map(x=>Math.max(0,Math.min(duration-.01,x))))]){
      video.currentTime=second;await wait('seeked');ctx.drawImage(video,0,0,9,8);
      const data=ctx.getImageData(0,0,9,8).data;let bits='';
      for(let y=0;y<8;y++)for(let x=0;x<8;x++){
        const i=(y*9+x)*4,j=i+4;
        const l=.299*data[i]+.587*data[i+1]+.114*data[i+2];
        const r=.299*data[j]+.587*data[j+1]+.114*data[j+2];bits+=l>r?'1':'0';
      }
      hashes.push(BigInt('0b'+bits).toString(16).padStart(16,'0'));
    }
    visual=JSON.stringify({algorithm:'sampled-dhash-9x8-v1',duration_seconds:Math.round(duration),samples:hashes});
  }catch{ /* Some formats are not browser-decodable; exact-file hash still useful. */ }
  finally {video.pause();video.removeAttribute('src');video.load();URL.revokeObjectURL(url)}
  return {sha256,visual,note:visual?'Browser visual samples ready; untrusted and not rights proof.':'Visual sampling unavailable for this codec.'};
}
