// POST /api/events: anonieme totaaltellingen per dag, pagina en actie (geen cookies, geen IP).
const EVENTS=new Set(['page_view','quote_cta','quote_start','quote_sent','whatsapp_click','phone_click']);
const json=(value,status=200)=>Response.json(value,{status,headers:{'Cache-Control':'private, no-store'}});
const localDay=()=>new Intl.DateTimeFormat('en-CA',{timeZone:'Europe/Amsterdam',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());

export async function onRequestPost({request,env,waitUntil}){
 if(!env.DB)return json({ok:false},503);
 if(request.headers.get('origin')&&request.headers.get('origin')!==new URL(request.url).origin)return json({error:'Ongeldige herkomst.'},403);
 if(Number(request.headers.get('content-length')||0)>2000)return json({error:'Ongeldige invoer.'},400);
 let input;try{input=await request.json();}catch{return json({error:'Ongeldige invoer.'},400);}
 const event=typeof input?.event==='string'?input.event:'';
 const path=typeof input?.path==='string'?input.path.split('?')[0].split('#')[0]:'';
 if(!EVENTS.has(event)||!/^\/[\w\-\/]{0,120}$/.test(path))return json({error:'Ongeldige meting.'},400);
 try{
  await env.DB.prepare('INSERT INTO site_events (day,path,event,count) VALUES (?,?,?,1) ON CONFLICT(day,path,event) DO UPDATE SET count=count+1').bind(localDay(),path,event).run();
  waitUntil(env.DB.prepare('DELETE FROM site_events WHERE day<?').bind(new Intl.DateTimeFormat('en-CA',{timeZone:'Europe/Amsterdam'}).format(new Date(Date.now()-427*86400000))).run().catch(()=>{}));
 }catch{return json({ok:false},503);}
 return json({ok:true},202);
}
