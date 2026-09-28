import test from 'node:test';
import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync,readdirSync} from 'node:fs';
import {createWorker,dates,validate} from '../worker/index.js';
import {confirmAppointment,validMoment} from '../worker/confirmation.js';

export function setup(){
 const sqlite=new DatabaseSync(':memory:');
 for(const file of readdirSync('drizzle').filter(f=>f.endsWith('.sql')))sqlite.exec(readFileSync('drizzle/'+file,'utf8'));
 const env={APPOINTMENT_ADMIN_EMAIL:'owner@example.test',DB:{prepare(sql){const stmt=sqlite.prepare(sql);let args=[];return {bind(...values){args=values;return this;},async first(){return stmt.get(...args)||null;},async all(){return {results:stmt.all(...args)};},async run(){const result=stmt.run(...args);return {meta:{changes:result.changes}};}};}},ASSETS:{fetch:async()=>new Response('static page')}};
 const worker=createWorker('<h1>Private manager</h1>',{routes:['/','/afspraak/','/bedankt/afspraak/','/404/']});
 return {sqlite,env,worker};
}
const valid=()=>({requestKey:crypto.randomUUID(),name:'Test Klant',email:'test@example.test',phone:'0612345678',address:'Teststraat 1',city:'Oldebroek',service:'Binnenschilderwerk',preferredDate:dates().min,period:'Geen voorkeur',notes:'Testaanvraag',website:''});
const req=(path,body,extra={},method='POST')=>new Request('https://site.test'+path,{method,headers:{origin:'https://site.test','content-type':'application/json','cf-connecting-ip':'127.0.0.1',...extra},...(body?{body:JSON.stringify(body)}:{})});

test('Amsterdam dates handle midnight and reject invalid, past and distant dates',()=>{
 assert.equal(dates(new Date('2026-09-23T23:30:00Z')).min,'2026-09-25');
 const range={min:'2026-02-01',max:'2026-05-01'};
 for(const date of ['2026-02-30','2026-01-31','2026-05-02','x'])assert.ok(validate({...valid(),preferredDate:date},range));
 assert.equal(validate({...valid(),preferredDate:'2026-03-01'},range),null);
});
test('saves a request persistently and retries without duplicates',async()=>{
 const {worker,env,sqlite}=setup(),body=valid();
 const first=await worker.fetch(req('/api/appointments',body),env);assert.equal(first.status,201);
 const result=await first.json();const repeat=await worker.fetch(req('/api/appointments',body),env);assert.equal((await repeat.json()).id,result.id);
 assert.equal(sqlite.prepare('SELECT count(*) AS n FROM appointment_requests').get().n,1);
 assert.equal(sqlite.prepare('SELECT status FROM appointment_requests').get().status,'nieuw');
 const afterRestart=createWorker();const list=await afterRestart.fetch(req('/api/admin/appointments',null,{'oai-authenticated-user-email':'owner@example.test'},'GET'),env);
 assert.equal((await list.json()).items[0].id,result.id);sqlite.close();
});
test('unauthorized users and cross-origin changes cannot read or mutate requests',async()=>{
 const {worker,env,sqlite}=setup();
 for(const headers of [{},{'oai-authenticated-user-email':'other@example.test'}])assert.equal((await worker.fetch(req('/api/admin/appointments',null,headers,'GET'),env)).status,403);
 assert.equal((await worker.fetch(req('/api/appointments',valid(),{origin:'https://other.test'}),env)).status,403);
 assert.equal((await worker.fetch(new Request('https://site.test/afspraken-beheer/'),env)).status,403);
 sqlite.close();
});
test('status changes cannot bypass the explicit email confirmation action',async()=>{
 const {worker,env,sqlite}=setup();const created=await (await worker.fetch(req('/api/appointments',valid()),env)).json();
 const path='/api/admin/appointments/'+created.id,headers={'oai-authenticated-user-email':'owner@example.test'};
 assert.equal((await worker.fetch(req(path,{status:'bevestigd'},headers,'PATCH'),env)).status,400);
 assert.equal((await worker.fetch(req(path,{status:'bevestigd',confirmedWithCustomer:true},headers,'PATCH'),env)).status,400);
 assert.equal((await worker.fetch(req(path,{status:'in_overleg'},headers,'PATCH'),env)).status,200);
 assert.equal(sqlite.prepare('SELECT status FROM appointment_requests').get().status,'in_overleg');
 assert.equal((await worker.fetch(req(path+'/confirm',{approved:true,date:dates().min,time:'10:00'},headers),env)).status,503);
 assert.equal((await worker.fetch(req(path+'/confirm',{approved:true,date:dates().min,time:'10:00'}),env)).status,403);
 assert.equal((await worker.fetch(req(path+'/confirm',{approved:true,date:dates().min,time:'10:00'},{...headers,origin:'https://attacker.test'}),env)).status,403);
 sqlite.close();
});
test('invalid payloads and excess requests are rejected; storage failures are honest',async()=>{
 const {worker,env,sqlite}=setup();
 assert.equal((await worker.fetch(req('/api/appointments',{...valid(),email:'invalid'}),env)).status,400);
 for(let i=0;i<8;i++)assert.equal((await worker.fetch(req('/api/appointments',valid()),env)).status,201);
 assert.equal((await worker.fetch(req('/api/appointments',valid()),env)).status,429);
 const missingDB={...env,DB:null};assert.equal((await worker.fetch(req('/api/appointments',valid()),missingDB)).status,503);sqlite.close();
});

test('cookie-free analytics stores only aggregate counters and protects the dashboard',async()=>{
 const {worker,env,sqlite}=setup();
 assert.equal((await worker.fetch(req('/api/events',{event:'page_view',path:'/'}),env)).status,202);
 assert.equal((await worker.fetch(req('/api/events',{event:'page_view',path:'/'}),env)).status,202);
 assert.equal((await worker.fetch(req('/api/events',{event:'phone_click',path:'/'}),env)).status,202);
 assert.equal(sqlite.prepare("SELECT count FROM site_events WHERE path='/' AND event='page_view'").get().count,2);
 assert.equal((await worker.fetch(req('/api/events',{event:'unknown',path:'/'}),env)).status,400);
 assert.equal((await worker.fetch(req('/api/events',{event:'page_view',path:'https://attacker.test'}),env)).status,400);
 assert.equal((await worker.fetch(req('/api/admin/analytics?days=30',null,{},'GET'),env)).status,403);
 const report=await (await worker.fetch(req('/api/admin/analytics?days=30',null,{'oai-authenticated-user-email':'owner@example.test'},'GET'),env)).json();
 assert.equal(report.totals.page_view,2);assert.equal(report.totals.phone_click,1);assert.deepEqual(report.pages,[{path:'/',count:2}]);
 assert.deepEqual(Object.keys(sqlite.prepare('PRAGMA table_info(site_events)').all()[0]),['cid','name','type','notnull','dflt_value','pk']);
 sqlite.close();
});

test('email confirmation requires approval and configuration and uses the stored recipient',async()=>{
 const {worker,env,sqlite}=setup();
 const created=await (await worker.fetch(req('/api/appointments',valid()),env)).json();
 const input={approved:true,date:dates().min,time:'10:30',email:'attacker@example.test'};
 let calls=0;const sent=[];
 const transport=async(url,options)=>{calls++;sent.push(JSON.parse(options.body));assert.equal(options.headers['Idempotency-Key'],'appointment-confirmation/'+created.id);return Response.json({id:'provider-message-id'});};
 assert.equal((await confirmAppointment(created.id,input,env,transport)).status,503);
 env.RESEND_API_KEY='test-only';env.CONFIRMATION_EMAIL_FROM='Van Ommen <info@example.test>';
 assert.equal((await confirmAppointment(created.id,{...input,approved:false},env,transport)).status,400);
 assert.equal(calls,0);
 assert.equal((await confirmAppointment(created.id,input,env,transport)).status,200);
 assert.equal((await confirmAppointment(created.id,input,env,transport)).body.alreadySent,true);
 assert.equal(calls,1);assert.deepEqual(sent[0].to,['test@example.test']);
 assert.match(sent[0].text,/10:30/);assert.match(sent[0].text,/Teststraat 1/);
 assert.equal(sqlite.prepare('SELECT status FROM appointment_requests').get().status,'bevestigd');
 assert.equal((await confirmAppointment(created.id,{...input,time:'11:00'},env,transport)).status,409);
 sqlite.close();
});

test('uncertain sends freeze the payload, block status edits and stop retries before key expiry',async()=>{
 const {worker,env,sqlite}=setup();
 const created=await (await worker.fetch(req('/api/appointments',valid()),env)).json();
 Object.assign(env,{RESEND_API_KEY:'test-only',CONFIRMATION_EMAIL_FROM:'info@example.test'});
 const input={approved:true,date:dates().min,time:'09:00'},payloads=[];
 const timeout=async(url,options)=>{payloads.push(options.body);throw new Error('timeout');};
 assert.equal((await confirmAppointment(created.id,input,env,timeout)).status,502);
 assert.equal(sqlite.prepare('SELECT status FROM appointment_requests').get().status,'nieuw');
 assert.equal((await confirmAppointment(created.id,{...input,time:'12:00'},env,timeout)).status,409);
 assert.equal((await worker.fetch(req('/api/admin/appointments/'+created.id,{status:'geannuleerd'},{'oai-authenticated-user-email':'owner@example.test'},'PATCH'),env)).status,409);
 await confirmAppointment(created.id,input,env,timeout);assert.equal(payloads[0],payloads[1]);
 sqlite.prepare('UPDATE appointment_requests SET confirmation_started_at=?').run(Date.now()-24*3600000);
 assert.equal((await confirmAppointment(created.id,input,env,timeout)).status,409);assert.equal(payloads.length,2);
 sqlite.close();
});

test('Dutch appointment time validation rejects invalid, past and ambiguous DST times',()=>{
 const now=new Date('2026-01-01T00:00:00Z');
 assert.equal(validMoment('2026-06-01','10:30',now),true);
 for(const [date,time] of [['2026-02-30','10:30'],['2026-06-01','25:00'],['2025-12-31','12:00'],['2026-03-29','02:30'],['2026-10-25','02:30']])assert.equal(validMoment(date,time,now),false);
});
