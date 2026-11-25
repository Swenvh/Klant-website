import test from 'node:test';
import assert from 'node:assert/strict';
import {normalize,validate,mailToOwner,mailToCustomer,verifyTurnstile,sendMail,SERVICES} from '../functions/_lib/offerte.js';

const goed={name:'Jan de Vries',email:'Jan@Voorbeeld.nl',phone:'06 12345678',city:'Elburg',type:'Particulier',service:'Buitenschilderwerk',requestKey:'3b241101-e2bb-4255-8caf-4136c566a962'};

test('een correcte aanvraag wordt geaccepteerd en genormaliseerd',()=>{
 const data=normalize({...goed,onbekend:'x',name:'  Jan de Vries '});
 assert.equal(validate(data),null);
 assert.equal(data.email,'jan@voorbeeld.nl');
 assert.equal(data.name,'Jan de Vries');
 assert.equal('onbekend' in data,false);
});
test('verplichte velden en formaten worden gecontroleerd',()=>{
 assert.match(validate(normalize({...goed,name:'J'})),/naam/);
 assert.match(validate(normalize({...goed,email:'geen-adres'})),/e-mailadres/);
 assert.match(validate(normalize({...goed,phone:'abc'})),/telefoonnummer/);
 assert.equal(validate(normalize({...goed,phone:''})),null);
 assert.match(validate(normalize({...goed,service:'Dakdekken'})),/werkzaamheden/);
 assert.match(validate(normalize({...goed,type:'Overheid'})),/particulier, zakelijk/);
 assert.match(validate(normalize({...goed,requestKey:'nee'})),/Vernieuw/);
 assert.match(validate(normalize({...goed,website:'http://spam'})),/niet worden verwerkt/);
 assert.equal(SERVICES.length,8);
});
test('mails bevatten de aanvraag en het antwoordadres',()=>{
 const data=normalize(goed);
 const owner=mailToOwner(data,{from:'Site <site@voorbeeld.nl>',to:'stef@voorbeeld.nl',id:'abc'});
 assert.equal(owner.reply_to,'jan@voorbeeld.nl');
 assert.deepEqual(owner.to,['stef@voorbeeld.nl']);
 assert.match(owner.subject,/Buitenschilderwerk in Elburg/);
 assert.equal('attachments' in owner,false);
 assert.match(owner.text,/Telefoon: 06 12345678/);
 const customer=mailToCustomer(data,{from:'Site <site@voorbeeld.nl>',id:'abc'});
 assert.deepEqual(customer.to,['jan@voorbeeld.nl']);
 assert.equal(customer.reply_to,'info@vanommenschilderwerken.nl');
 assert.equal('attachments' in customer,false);
 assert.match(customer.text,/Beste Jan de Vries/);
});
test('Turnstile en Resend worden alleen als geslaagd gezien bij een geldig antwoord',async()=>{
 const ok=async()=>({ok:true,json:async()=>({success:true,id:'mail_1'})});
 const fail=async()=>({ok:false,json:async()=>({success:false})});
 assert.equal(await verifyTurnstile('token','geheim','1.2.3.4',ok),true);
 assert.equal(await verifyTurnstile('token','geheim','1.2.3.4',fail),false);
 assert.equal(await verifyTurnstile('','geheim','1.2.3.4',ok),false);
 assert.equal(await sendMail({},'sleutel','k',ok),'mail_1');
 assert.equal(await sendMail({},'sleutel','k',fail),null);
 assert.equal(await sendMail({},'sleutel','k',async()=>{throw new Error('netwerk');}),null);
});
