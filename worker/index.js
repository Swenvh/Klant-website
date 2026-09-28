import {confirmAppointment,mailReady} from './confirmation.js';
const PERIODS=['Ochtend (09:00–12:00)','Middag (13:00–17:00)','Geen voorkeur'];
const SERVICES=['Binnenschilderwerk','Buitenschilderwerk','Houtwerk & onderhoud','Kleur & afwerking','Meerdere werkzaamheden / ik weet het nog niet'];
const STATUS=['nieuw','in_overleg','bevestigd','afgerond','geannuleerd'];
const EVENTS=['page_view','quote_cta','quote_start','quote_mail_open','whatsapp_click','phone_click','appointment_cta','appointment_start','appointment_saved'];
const json=(value,status=200)=>Response.json(value,{status,headers:{'Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff'}});
const db=env=>{if(!env.DB)throw new Error('Database unavailable');return env.DB;};
const localDay=(date=new Date())=>new Intl.DateTimeFormat('en-CA',{timeZone:'Europe/Amsterdam',year:'numeric',month:'2-digit',day:'2-digit'}).format(date);
async function cleanup(env,now=Date.now()){
 const appointmentCutoff=now-365*86400000;
 const analyticsCutoff=localDay(new Date(now-427*86400000));
 await env.DB.prepare('DELETE FROM appointment_requests WHERE updated_at<?').bind(appointmentCutoff).run();
 await env.DB.prepare('DELETE FROM site_events WHERE day<?').bind(analyticsCutoff).run();
}
export function dates(now=new Date()){
 const parts=new Intl.DateTimeFormat('en-CA',{timeZone:'Europe/Amsterdam',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(now);
 const get=t=>parts.find(x=>x.type===t).value;
 const today=`${get('year')}-${get('month')}-${get('day')}`;
 const add=n=>new Date(Date.parse(today+'T12:00:00Z')+n*86400000).toISOString().slice(0,10);
 return {min:add(1),max:add(90),periods:PERIODS};
}
export function validate(input,range=dates()){
 if(!input || typeof input!=='object' || Array.isArray(input))return 'Controleer uw gegevens.';
 for(const [name,min,max] of [['name',2,100],['email',3,150],['phone',6,30],['address',3,200],['city',2,100],['notes',0,2000]]){
  if(typeof input[name]!=='string'||input[name].trim().length<min||input[name].length>max)return 'Vul alle verplichte velden correct in.';
 }
 if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input.email))return 'Vul een geldig e-mailadres in.';
 if(!/^[+\d ()-]{6,30}$/.test(input.phone)||input.phone.replace(/\D/g,'').length<6)return 'Vul een geldig telefoonnummer in.';
 if(!SERVICES.includes(input.service)||!PERIODS.includes(input.period))return 'Kies de werkzaamheden en uw voorkeursmoment.';
 if(typeof input.preferredDate!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(input.preferredDate))return 'Kies een datum.';
 const date=new Date(input.preferredDate+'T12:00:00Z');
 if(!Number.isFinite(date.getTime())||date.toISOString().slice(0,10)!==input.preferredDate||input.preferredDate<range.min||input.preferredDate>range.max)return 'Kies een datum vanaf morgen, binnen de komende drie maanden.';
 if(!/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(input.requestKey||''))return 'Vernieuw de pagina en probeer opnieuw.';
 if(input.website)return 'De aanvraag kon niet worden verwerkt. Bel Stef gerust.';
 return null;
}
function admin(request,env){
 const email=request.headers.get('oai-authenticated-user-email');
 return !!email && !!env.APPOINTMENT_ADMIN_EMAIL && email.toLowerCase()===env.APPOINTMENT_ADMIN_EMAIL.toLowerCase();
}
function sameOrigin(request){
 const allowed=new Set([new URL(request.url).origin,'https://van-ommen-schilderwerken.ecomswen.chatgpt.site','https://preview.vanommenschilderwerken.nl']);
 return allowed.has(request.headers.get('origin'));
}
async function readJSON(request){
 if(!request.headers.get('content-type')?.includes('application/json'))throw new Error('invalid body');
 const reader=request.body?.getReader();if(!reader)throw new Error('invalid body');
 let length=0;const chunks=[];
 while(true){const {done,value}=await reader.read();if(done)break;length+=value.length;if(length>12000){await reader.cancel();throw new Error('invalid body');}chunks.push(value);}
 const bytes=new Uint8Array(length);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length;}
 return JSON.parse(new TextDecoder().decode(bytes));
}
async function throttle(request,env){
 const ip=request.headers.get('cf-connecting-ip')||'unknown';
 const time=Math.floor(Date.now()/3600000);
 const hash=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(ip+':'+time));
 const bucket=Array.from(new Uint8Array(hash),b=>b.toString(16).padStart(2,'0')).join('');
 const row=await db(env).prepare('INSERT INTO appointment_request_limits (bucket,count,expires_at) VALUES (?,1,?) ON CONFLICT(bucket) DO UPDATE SET count=count+1 WHERE count<8 RETURNING count').bind(bucket,(time+2)*3600000).first();
 return !!row;
}
export function createWorker(adminHTML='',seo={routes:[]}){
 return {async fetch(request,env,ctx){
  const url=new URL(request.url),path=url.pathname;
  const local=['localhost','127.0.0.1','[::1]'].includes(url.hostname);
  const canonicalPath=path.toLowerCase().replace(/\/{2,}/g,'/').replace(/\/index\.html$/,'/').replace(/\.html$/,'').replace(/\/?$/,'/');
  if(!local&&url.protocol==='http:'){
   url.protocol='https:';
   if(seo.routes.includes(canonicalPath))url.pathname=canonicalPath;
   return Response.redirect(url.href,308);
  }
  if(['GET','HEAD'].includes(request.method)&&seo.routes.includes(canonicalPath)&&path!==canonicalPath){
   url.pathname=canonicalPath;return Response.redirect(url.href,308);
  }
  try{
   if(path==='/api/events'&&request.method==='POST'){
    if(!sameOrigin(request))return json({error:'Ongeldige herkomst.'},403);
    let input;try{input=await readJSON(request);}catch{return json({error:'Ongeldige invoer.'},400);}
    const event=typeof input?.event==='string'?input.event:'';
    const eventPath=typeof input?.path==='string'?input.path.split('?')[0]:'';
    if(!EVENTS.includes(event)||!seo.routes.includes(eventPath))return json({error:'Ongeldige meting.'},400);
    const day=localDay();
    await db(env).prepare('INSERT INTO site_events (day,path,event,count) VALUES (?,?,?,1) ON CONFLICT(day,path,event) DO UPDATE SET count=count+1').bind(day,eventPath,event).run();
    return json({ok:true},202);
   }
   if(path==='/api/appointments/options'&&request.method==='GET')return json(dates());
   if(path==='/api/appointments'&&request.method==='POST'){
    if(!sameOrigin(request))return json({error:'Open de planner op de website en probeer opnieuw.'},403);
    let input;try{input=await readJSON(request);}catch{return json({error:'De aanvraag is ongeldig of te groot.'},400);}
    const error=validate(input);if(error)return json({error},400);
    const existing=await db(env).prepare('SELECT id FROM appointment_requests WHERE request_key=?').bind(input.requestKey).first();
    if(existing)return json({id:existing.id,status:'aangevraagd'},200);
    if(!await throttle(request,env))return json({error:'U heeft meerdere aanvragen gedaan. Probeer het later opnieuw of bel Stef.'},429);
    const id=crypto.randomUUID(),now=Date.now();
    await db(env).prepare('INSERT INTO appointment_requests (id,request_key,name,email,phone,address,city,service,preferred_date,period,notes,status,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,\'nieuw\',?,?) ON CONFLICT(request_key) DO NOTHING').bind(id,input.requestKey,input.name.trim(),input.email.trim().toLowerCase(),input.phone.trim(),input.address.trim(),input.city.trim(),input.service,input.preferredDate,input.period,input.notes.trim(),now,now).run();
    const saved=await db(env).prepare('SELECT id FROM appointment_requests WHERE request_key=?').bind(input.requestKey).first();
    ctx?.waitUntil(Promise.all([db(env).prepare('DELETE FROM appointment_request_limits WHERE expires_at<?').bind(now).run(),cleanup(env,now)]).catch(()=>{}));
    return json({id:saved.id,status:'aangevraagd'},201);
   }
   if(path.startsWith('/api/admin/')){
    if(!admin(request,env))return json({error:'Alleen de beheerder kan deze aanvragen bekijken.'},403);
    if(path==='/api/admin/analytics'&&request.method==='GET'){
     const days=Math.min(90,Math.max(7,Number(url.searchParams.get('days')||30)||30));
     const since=localDay(new Date(Date.now()-(days-1)*86400000));
     const totals=await db(env).prepare('SELECT event,SUM(count) AS count FROM site_events WHERE day>=? GROUP BY event').bind(since).all();
     const pages=await db(env).prepare("SELECT path,SUM(count) AS count FROM site_events WHERE day>=? AND event='page_view' GROUP BY path ORDER BY count DESC LIMIT 10").bind(since).all();
     ctx?.waitUntil(cleanup(env).catch(()=>{}));
     return json({days,totals:Object.fromEntries(totals.results.map(row=>[row.event,row.count])),pages:pages.results});
    }
    if(path==='/api/admin/appointments'&&request.method==='GET'){
     const cursor=Number(url.searchParams.get('before')||Date.now()+1);
     if(!Number.isSafeInteger(cursor)||cursor<0)return json({error:'Ongeldige pagina.'},400);
     const rows=await db(env).prepare('SELECT id,name,email,phone,address,city,service,preferred_date,period,notes,status,created_at,confirmed_date,confirmed_time,confirmation_started_at,confirmation_email_id FROM appointment_requests WHERE created_at<? ORDER BY created_at DESC LIMIT 51').bind(cursor).all();
     const items=rows.results.slice(0,50);return json({items,emailConfigured:mailReady(env),next:rows.results.length>50?items.at(-1).created_at:null});
    }
    if(request.method==='POST'&&/^\/api\/admin\/appointments\/[0-9a-f-]{36}\/confirm$/.test(path)){
     if(!sameOrigin(request))return json({error:'Ongeldige herkomst.'},403);
     let input;try{input=await readJSON(request);}catch{return json({error:'Ongeldige invoer.'},400);}
     const result=await confirmAppointment(path.split('/')[4],input,env);
     return json(result.body,result.status);
    }
    if(request.method==='PATCH'&&/^\/api\/admin\/appointments\/[0-9a-f-]{36}$/.test(path)){
     if(!sameOrigin(request))return json({error:'Ongeldige herkomst.'},403);
     let input;try{input=await readJSON(request);}catch{return json({error:'Ongeldige invoer.'},400);}
     if(!STATUS.includes(input?.status))return json({error:'Ongeldige status.'},400);
     if(input.status==='bevestigd')return json({error:'Gebruik Afspraak bevestigen en mail versturen met de definitieve datum en tijd.'},400);
     const result=await db(env).prepare('UPDATE appointment_requests SET status=?,updated_at=? WHERE id=? AND (confirmation_payload IS NULL OR confirmation_email_id IS NOT NULL)').bind(input.status,Date.now(),path.split('/').pop()).run();
     return result.meta.changes?json({ok:true}):json({error:'Aanvraag niet gevonden of mailverzending nog onzeker. Controleer eerst de verzendstatus.'},409);
    }
    return json({error:'Niet gevonden.'},404);
   }
   if(path==='/afspraken-beheer/'||path==='/afspraken-beheer'){
    if(!admin(request,env))return new Response('<!doctype html><html lang="nl"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Beheer aanvragen</title><body><h1>Beheer van aanvragen</h1><p>Deze pagina is alleen beschikbaar voor de beheerder.</p><a href="/signin-with-chatgpt?return_to=%2Fafspraken-beheer%2F" target="_top">Inloggen als beheerder</a><p><a href="/">Terug naar de website</a></p></body></html>',{status:403,headers:{'Content-Type':'text/html; charset=utf-8','Cache-Control':'private, no-store','X-Robots-Tag':'noindex'}});
    return new Response(adminHTML,{headers:{'Content-Type':'text/html; charset=utf-8','Cache-Control':'private, no-store','X-Robots-Tag':'noindex'}});
   }
   if(path.startsWith('/api/'))return json({error:'Niet gevonden.'},404);
   let response=await env.ASSETS.fetch(request);
   if(response.status===404&&['GET','HEAD'].includes(request.method)&&!path.startsWith('/assets/')){
    const fallback=await env.ASSETS.fetch(new Request(new URL('/404/',request.url),request));
    response=new Response(request.method==='HEAD'?null:fallback.body,{status:404,headers:fallback.headers});
   }
   const headers=new Headers(response.headers);
   headers.set('Strict-Transport-Security','max-age=31536000');
   headers.set('X-Content-Type-Options','nosniff');
   headers.set('Referrer-Policy','strict-origin-when-cross-origin');
   headers.set('Permissions-Policy','camera=(), microphone=(), geolocation=()');
   if(response.status===404)headers.set('X-Robots-Tag','noindex, nofollow');
   if(path.startsWith('/assets/'))headers.set('Cache-Control','public, max-age=604800');
   else if(/\.(css|js)$/.test(path))headers.set('Cache-Control','public, max-age=3600, must-revalidate');
   else headers.set('Cache-Control','public, max-age=0, must-revalidate');
   if(path==='/llms.txt'||path==='/robots.txt')headers.set('Content-Type','text/plain; charset=utf-8');
   if(path==='/sitemap.xml')headers.set('Content-Type','application/xml; charset=utf-8');
   return new Response(response.body,{status:response.status,headers});
  }catch(error){
   console.error('Appointment service unavailable',error?.name||'Error');
   return json({error:'Opslaan lukt op dit moment niet. Uw gegevens blijven ingevuld. Probeer opnieuw of bel 06 24 99 67 00.'},503);
  }
 }};
}
export default createWorker();
