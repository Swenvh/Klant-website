const form=document.querySelector('#appointment-form');
if(form){
 const error=document.querySelector('#appointment-error');
 const submit=form.querySelector('[type="submit"]');
 const requestKey=crypto.randomUUID();
 let trackedStart=false;
 form.addEventListener('focusin',()=>{if(!trackedStart){trackedStart=true;window.vosTrack?.('appointment_start');}});
 const showError=message=>{error.textContent=message;error.hidden=false;};
 fetch('/api/appointments/options').then(async response=>{
  if(!response.ok)throw new Error();
  const options=await response.json();
  const date=form.elements.preferredDate;date.min=options.min;date.max=options.max;
  document.querySelector('#appointment-loading').hidden=true;submit.disabled=false;
 }).catch(()=>{document.querySelector('#appointment-loading').hidden=true;showError('De planner kan nu niet laden. Vernieuw de pagina of bel 06 24 99 67 00.');});
 form.addEventListener('submit',async event=>{
  event.preventDefault();if(!form.reportValidity())return;
  error.hidden=true;submit.disabled=true;submit.textContent='Aanvraag opslaan…';
  const data=Object.fromEntries(new FormData(form));data.requestKey=requestKey;
  try{
   const response=await fetch('/api/appointments',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
   const result=await response.json();if(!response.ok)throw new Error(result.error||'Opslaan is niet gelukt. Probeer opnieuw.');
   const date=new Date(data.preferredDate+'T12:00:00').toLocaleDateString('nl-NL',{weekday:'long',day:'numeric',month:'long',year:'numeric'});
   document.querySelector('#appointment-summary').textContent=`Uw voorkeur: ${date}, ${data.period.toLowerCase()}. Werkzaamheden: ${data.service}.`;
   const message=`Beste Stef, ik heb via de website een afspraak aangevraagd. Mijn naam is ${data.name}. Mijn voorkeur is ${date}, ${data.period.toLowerCase()}, voor ${data.service.toLowerCase()} in ${data.city}. Kunnen we dit moment afstemmen? Aanvraag: ${result.id.slice(0,8)}.`;
   document.querySelector('#appointment-whatsapp').href='https://wa.me/31624996700?text='+encodeURIComponent(message);
   window.vosTrack?.('appointment_saved');window.location.assign('/bedankt/afspraak/');return;
  }catch(reason){showError(reason.message==='Failed to fetch'?'Geen verbinding. Uw gegevens blijven ingevuld. Probeer opnieuw of bel Stef.':reason.message);}
  finally{submit.disabled=false;submit.textContent='Afspraak aanvragen';}
 });
}

const list=document.querySelector('#appointment-list');
if(list){
 const status=document.querySelector('#admin-status'),more=document.querySelector('#more-appointments');
 let next=null,emailConfigured=false;
 const states={nieuw:'Nieuw',in_overleg:'In overleg',bevestigd:'Afgesproken met klant',afgerond:'Afgerond',geannuleerd:'Geannuleerd'};
 const element=(tag,text,className)=>{const el=document.createElement(tag);if(text)el.textContent=text;if(className)el.className=className;return el;};
 function card(item){
  const article=element('article',null,'appointment-card');
  article.append(element('h2',item.name));
  const date=new Date(item.preferred_date+'T12:00:00').toLocaleDateString('nl-NL',{day:'numeric',month:'long',year:'numeric'});
  article.append(element('p',`Voorkeur: ${date} · ${item.period}`,'appointment-preference'));
  article.append(element('p',`${item.service} — ${item.address}, ${item.city}`));
  if(item.notes)article.append(element('p',item.notes,'appointment-notes'));
  article.append(element('p','Ontvangen: '+new Date(item.created_at).toLocaleString('nl-NL',{timeZone:'Europe/Amsterdam'}),'field-help'));
  const links=element('div',null,'admin-toolbar');
  const phone=element('a','Bel '+item.phone,'text-link');phone.href='tel:'+item.phone.replace(/[^+\d]/g,'');
  const email=element('a','E-mail '+item.email,'text-link');email.href='mailto:'+encodeURIComponent(item.email)+'?subject='+encodeURIComponent('Uw afspraakaanvraag bij Van Ommen Schilderwerken');
  links.append(phone,email);article.append(links);
  const update=element('form',null,'admin-update');const label=element('label','Status van deze aanvraag');const select=document.createElement('select');
  for(const [value,text] of Object.entries(states)){const option=element('option',text);option.value=value;option.disabled=value==='bevestigd';select.append(option);}select.value=item.status;label.append(select);
  const button=element('button','Status opslaan','button');button.type='submit';const feedback=element('p');feedback.setAttribute('role','status');
  update.append(label,button,feedback);
  update.addEventListener('submit',async event=>{
   event.preventDefault();if(select.value==='bevestigd'){feedback.textContent='Deze afspraak is al bevestigd. Kies alleen een andere status als die is gewijzigd.';return;}
   button.disabled=true;
   try{const response=await fetch('/api/admin/appointments/'+item.id,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({status:select.value})});const result=await response.json();if(!response.ok)throw new Error(result.error);feedback.textContent='Opgeslagen. Er is geen bericht verstuurd aan de klant.';}catch(e){feedback.textContent=e.message||'Opslaan mislukt.';}finally{button.disabled=false;}
  });article.append(update);
  article.append(element('h3','Bevestigingsmail aan de klant'));
  if(item.confirmation_email_id){
   article.append(element('p',`Afgesproken: ${item.confirmed_date} om ${item.confirmed_time} uur (Nederlandse tijd). De verzenddienst heeft de bevestigingsmail geaccepteerd. Dit is geen ontvangst- of leesbevestiging.`));
   article.append(element('p','Wilt u wijzigen of annuleren? Stem dit rechtstreeks met de klant af. Een statuswijziging verstuurt geen nieuwe mail.'));
  }else if(!['geannuleerd','afgerond'].includes(item.status)){
   const mailForm=element('form',null,'confirmation-form');
   const dateLabel=element('label','Definitieve datum'),timeLabel=element('label','Definitieve tijd (Nederlandse tijd)');
   const chosenDate=document.createElement('input'),chosenTime=document.createElement('input');
   chosenDate.type='date';chosenDate.required=true;chosenDate.value=item.confirmed_date||item.preferred_date;
   chosenTime.type='time';chosenTime.required=true;chosenTime.value=item.confirmed_time||'';
   chosenDate.readOnly=chosenTime.readOnly=Boolean(item.confirmation_started_at);
   dateLabel.append(chosenDate);timeLabel.append(chosenTime);
   const moment=element('div',null,'form-row');moment.append(dateLabel,timeLabel);
   const preview=element('p');
   const describe=()=>{preview.textContent=`De mail gaat naar ${item.email} en bevestigt het bezoek op ${chosenDate.value||'de gekozen datum'} om ${chosenTime.value||'de gekozen tijd'}, aan ${item.address}, ${item.city}, voor ${item.service.toLowerCase()}. De klant kan per e-mail of telefoon reageren om te wijzigen of annuleren.`;};
   chosenDate.addEventListener('input',describe);chosenTime.addEventListener('input',describe);describe();
   const approveLabel=element('label',null,'admin-confirmation'),approve=document.createElement('input');approve.type='checkbox';approve.required=true;
   approveLabel.append(approve,document.createTextNode('Ik heb de gegevens gecontroleerd, geef akkoord op deze afspraak en wil de bevestigingsmail aan deze klant versturen.'));
   const send=element('button',item.confirmation_started_at?'Bevestigingsmail opnieuw proberen':'Afspraak bevestigen en mail versturen','button');send.type='submit';send.disabled=!emailConfigured;
   const resultText=element('p');resultText.setAttribute('role','status');
   if(item.confirmation_started_at)resultText.textContent='De vorige verzendpoging is nog niet bevestigd. Probeer hetzelfde bericht opnieuw of controleer de verzenddienst.';
   mailForm.append(moment,preview,approveLabel,send,resultText);
   mailForm.addEventListener('submit',async event=>{
    event.preventDefault();if(!mailForm.reportValidity())return;
    send.disabled=true;button.disabled=true;resultText.textContent='Bevestigingsmail versturen…';
    try{
     const response=await fetch('/api/admin/appointments/'+item.id+'/confirm',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({date:chosenDate.value,time:chosenTime.value,approved:approve.checked})});
     const result=await response.json();if(!response.ok)throw new Error(result.error);
     resultText.textContent='Afspraak bevestigd. De verzenddienst heeft de mail geaccepteerd. Dit is geen ontvangst- of leesbevestiging.';
     select.value='bevestigd';chosenDate.readOnly=chosenTime.readOnly=true;approve.disabled=true;send.textContent='Bevestigingsmail verwerkt';
    }catch(e){resultText.textContent=e.message||'Verzendstatus onbekend. Vernieuw het overzicht voordat u opnieuw probeert.';send.disabled=!emailConfigured;send.textContent='Bevestigingsmail opnieuw proberen';}
    finally{button.disabled=false;}
   });article.append(mailForm);
  }
  return article;
 }
 async function load(append=false){
  status.textContent='Aanvragen laden…';more.disabled=true;
  try{const response=await fetch('/api/admin/appointments'+(append&&next?'?before='+next:''));const data=await response.json();if(!response.ok)throw new Error(data.error);emailConfigured=data.emailConfigured===true;document.querySelector('#admin-mail-status').textContent=emailConfigured?'De mailkoppeling is ingesteld. Controleer per afspraak de ontvanger en het definitieve moment.':'Bevestigingsmail is nog niet actief. Het afzenderadres en de verzenddienst moeten eerst worden gekoppeld. U kunt aanvragen wel bekijken en klanten zelf bellen of mailen.';if(!append)list.replaceChildren();for(const item of data.items)list.append(card(item));next=data.next;more.hidden=!next;status.textContent=list.children.length?`${list.children.length} aanvragen getoond.`:'Er zijn nog geen afspraakaanvragen.';}catch(e){status.textContent=e.message||'Laden mislukt. Probeer opnieuw.';}finally{more.disabled=false;}
 }
 document.querySelector('#refresh-appointments').addEventListener('click',()=>load());more.addEventListener('click',()=>load(true));load();
}

const analytics=document.querySelector('#analytics-summary');
if(analytics){
 const analyticsElement=(tag,text,className)=>{const el=document.createElement(tag);if(text)el.textContent=text;if(className)el.className=className;return el;};
 const labels={page_view:'Paginaweergaven',quote_cta:'Kliks naar offerte',quote_start:'Gestarte offerteformulieren',quote_mail_open:'Geopende e-mailaanvragen',whatsapp_click:'WhatsApp-kliks',phone_click:'Telefoonkliks',appointment_cta:'Kliks naar afspraak',appointment_start:'Gestarte afspraakaanvragen',appointment_saved:'Opgeslagen afspraakaanvragen'};
 fetch('/api/admin/analytics?days=30').then(async response=>{const data=await response.json();if(!response.ok)throw new Error(data.error);analytics.replaceChildren();for(const key of Object.keys(labels)){const item=analyticsElement('div',null,'analytics-metric');item.append(analyticsElement('strong',String(data.totals[key]||0)),analyticsElement('span',labels[key]));analytics.append(item);}const note=analyticsElement('p','Aantallen over de afgelopen 30 dagen. Dit zijn geen unieke bezoekers; herhaalde en geautomatiseerde bezoeken kunnen meetellen.','field-help');document.querySelector('#analytics-panel').append(note);const pages=document.querySelector('#analytics-pages');for(const row of data.pages){const li=analyticsElement('li',`${row.path} — ${row.count} weergaven`);pages.append(li);}}).catch(error=>{analytics.textContent=error.message||'Metingen kunnen nu niet worden geladen.';});
}
