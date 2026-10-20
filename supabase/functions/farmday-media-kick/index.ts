import { createClient } from "npm:@supabase/supabase-js@2";
const base = Deno.env.get("SUPABASE_URL")!;
const db = createClient(base, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!);
const cors = {"Access-Control-Allow-Origin":"*","Access-Control-Allow-Headers":"authorization,apikey,content-type,x-client-info","Access-Control-Allow-Methods":"POST,OPTIONS"};
const reply = (body:unknown,status=200) => new Response(JSON.stringify(body),{status,headers:{...cors,"content-type":"application/json","cache-control":"no-store"}});
Deno.serve(async req => {
  if(req.method==="OPTIONS")return new Response(null,{headers:cors});
  if(req.method!=="POST")return reply({error:"POST required"},405);
  try {
    const jwt=(req.headers.get("authorization")||"").replace(/^Bearer /,"");
    const {data:{user},error}=await db.auth.getUser(jwt);
    if(error||!user)return reply({error:"Unauthorized"},401);
    const body=await req.json().catch(()=>({}));
    const id=String(body.session_id||"");
    if(!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id))return reply({error:"Invalid session"},400);
    const {data:session,error:sessionError}=await db.from("farmday_youtube_upload_sessions").select("id,state").eq("id",id).eq("user_id",user.id).maybeSingle();
    if(sessionError||!session)return reply({error:"Session not found"},404);
    if(session.state!=="completed")return reply({queued:false,error:"YouTube upload is not complete"},409);
    const {data:preview}=await db.from("farmday_review_previews").select("session_id").eq("session_id",id).eq("user_id",user.id).maybeSingle();
    if(!preview)return reply({queued:false,error:"Private analysis original is missing"},409);
    const token=Deno.env.get("FARMDAY_GITHUB_DISPATCH_TOKEN");
    if(!token){console.error("FARMDAY_DISPATCH_MISSING_TOKEN",id);return reply({queued:true,immediate:false,error:"dispatch_token_missing",reason:"GitHub dispatch token is not configured"},503);}
    const response=await fetch("https://api.github.com/repos/joelndoci-farmday/farmday/dispatches",{
      method:"POST",headers:{"Authorization":"Bearer "+token,"Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28","User-Agent":"FarmDay-Media-Queue","Content-Type":"application/json"},
      body:JSON.stringify({event_type:"farmday_media_ready",client_payload:{session_id:id}})
    });
    if(!response.ok){console.error("FARMDAY_DISPATCH_REJECTED",response.status,id);return reply({queued:true,immediate:false,error:"dispatch_rejected",reason:"GitHub dispatch rejected (HTTP "+response.status+")"},502);}
    console.info("FARMDAY_DISPATCH_ACCEPTED",id,response.status);return reply({queued:true,immediate:true,reason:"Cloud analysis dispatch accepted"});
  }catch(error){console.error("media kick failed",error);return reply({error:"Cloud dispatch request failed"},500);}
});
