// POST /api/offerte: ontvangt het offerteformulier, bewaart de aanvraag in D1 en mailt Stef en de klant via Resend.
import {normalize,validate,mailToOwner,mailToCustomer,verifyTurnstile,sendMail,MAX_BODY_BYTES,OWNER_PHONE} from '../_lib/offerte.js';

const THANKS='/bedankt/offerte/';
const GENERIC='Versturen lukt op dit moment niet. Uw gegevens blijven ingevuld. Probeer het opnieuw of bel '+OWNER_PHONE+'.';
const json=(value,status=200)=>Response.json(value,{status,headers:{'Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff'}});
const wantsJSON=request=>(request.headers.get('accept')||'').includes('application/json');
const escapeHTML=s=>s.replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

function reply(request,status,error){
 if(wantsJSON(request))return json(error?{error}:{ok:true},status);
 if(!error)return Response.redirect(new URL(THANKS,request.url).href,303);
 const page=`<!doctype html><html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>Aanvraag niet verstuurd | Van Ommen Schilderwerken</title><style>body{font-family:Poppins,Arial,sans-serif;max-width:560px;margin:60px auto;padding:0 24px;line-height:1.7;color:#171717}a{color:inherit}</style></head><body><h1>De aanvraag is niet verstuurd</h1><p>${escapeHTML(error)}</p><p><a href="/offerte/">Terug naar het formulier</a></p></body></html>`;
 return new Response(page,{status,headers:{'Content-Type':'text/html; charset=utf-8','Cache-Control':'private, no-store'}});
}

async function throttle(request,env){
 const ip=request.headers.get('cf-connecting-ip')||'unknown';
 const hour=Math.floor(Date.now()/3600000);
 const hash=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(ip+':'+hour));
 const bucket=Array.from(new Uint8Array(hash),b=>b.toString(16).padStart(2,'0')).join('');
 const row=await env.DB.prepare('INSERT INTO request_limits (bucket,count,expires_at) VALUES (?,1,?) ON CONFLICT(bucket) DO UPDATE SET count=count+1 WHERE count<6 RETURNING count').bind(bucket,(hour+2)*3600000).first();
 return !!row;
}

export async function onRequestPost({request,env,waitUntil}){
 if(!env.DB)return reply(request,503,GENERIC);
 const length=Number(request.headers.get('content-length')||0);
 if(length>MAX_BODY_BYTES)return reply(request,413,'De aanvraag is te groot.');
 let form;
 try{form=await request.formData();}catch{return reply(request,400,'De aanvraag is ongeldig. Vernieuw de pagina en probeer opnieuw.');}
 const fields={};for(const [key,value] of form.entries())if(typeof value==='string')fields[key]=value;
 const data=normalize(fields);
 const error=validate(data);
 if(error)return reply(request,400,error);
 if(env.TURNSTILE_SECRET){
  const ok=await verifyTurnstile(fields['cf-turnstile-response'],env.TURNSTILE_SECRET,request.headers.get('cf-connecting-ip'));
  if(!ok)return reply(request,400,'De spamcontrole is niet gelukt. Vernieuw de pagina en probeer opnieuw, of bel '+OWNER_PHONE+'.');
 }
 const requestKey=data.requestKey||crypto.randomUUID();
 try{
  const existing=await env.DB.prepare('SELECT id FROM quote_requests WHERE request_key=?').bind(requestKey).first();
  if(existing)return reply(request,200,null);
  if(!await throttle(request,env))return reply(request,429,'U heeft al meerdere aanvragen gedaan. Probeer het later opnieuw of bel '+OWNER_PHONE+'.');
  const id=crypto.randomUUID(),now=Date.now();
  await env.DB.prepare('INSERT INTO quote_requests (id,request_key,name,email,phone,city,customer_type,service,status,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(request_key) DO NOTHING')
   .bind(id,requestKey,data.name,data.email,data.phone,data.city,data.type,data.service,'nieuw',now,now).run();
  const saved=await env.DB.prepare('SELECT id FROM quote_requests WHERE request_key=?').bind(requestKey).first();
  const mail=async()=>{
   if(!env.RESEND_API_KEY||!env.MAIL_FROM){await env.DB.prepare('UPDATE quote_requests SET status=? WHERE id=?').bind('mail_niet_ingesteld',saved.id).run();return;}
   const ownerId=await sendMail(mailToOwner(data,{from:env.MAIL_FROM,to:env.MAIL_TO,id:saved.id}),env.RESEND_API_KEY,'offerte-eigenaar/'+saved.id);
   const customerId=await sendMail(mailToCustomer(data,{from:env.MAIL_FROM,id:saved.id}),env.RESEND_API_KEY,'offerte-klant/'+saved.id);
   await env.DB.prepare('UPDATE quote_requests SET mail_owner_id=?,mail_customer_id=?,status=?,updated_at=? WHERE id=?').bind(ownerId,customerId,ownerId?'gemaild':'mail_mislukt',Date.now(),saved.id).run();
  };
  // De mail naar Stef moet weg zijn voordat we bevestigen; de rest mag na het antwoord.
  await mail();
  waitUntil(env.DB.prepare('DELETE FROM request_limits WHERE expires_at<?').bind(now).run().catch(()=>{}));
  return reply(request,201,null);
 }catch(error){
  console.error('offerte',error?.name||'Error',error?.message||'');
  return reply(request,503,GENERIC);
 }
}

export const onRequest=({request})=>request.method==='POST'?undefined:json({error:'Gebruik het formulier op /offerte/.'},405);
