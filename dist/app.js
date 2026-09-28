const menuButton = document.querySelector('.menu-toggle');
const mobileNav = document.querySelector('#mobile-nav');
function closeMenu(){menuButton.setAttribute('aria-expanded','false');menuButton.setAttribute('aria-label','Menu openen');mobileNav.hidden=true;}
menuButton.addEventListener('click',()=>{const opened=menuButton.getAttribute('aria-expanded')==='true';menuButton.setAttribute('aria-expanded',String(!opened));menuButton.setAttribute('aria-label',opened?'Menu openen':'Menu sluiten');mobileNav.hidden=opened;});
mobileNav.querySelectorAll('a').forEach(a=>a.addEventListener('click',closeMenu));
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!mobileNav.hidden){closeMenu();menuButton.focus();}});
window.matchMedia('(min-width:851px)').addEventListener('change',e=>{if(e.matches)closeMenu();});
document.querySelectorAll('.service-quote').forEach(a=>a.addEventListener('click',()=>{const select=document.querySelector('[name=service]');if(select)select.value=a.dataset.service;}));
document.querySelector('#offerte')?.addEventListener('submit',e=>{e.preventDefault();const form=e.currentTarget;if(!form.reportValidity())return;const d=new FormData(form);const body=`Beste Stef,\n\nGraag bespreek ik de volgende schilderwerkzaamheden.\n\nNaam: ${d.get('name')}\nWoonplaats: ${d.get('city')}\nE-mail: ${d.get('email')}\nTelefoon: ${d.get('phone')||'Niet ingevuld'}\nWerkzaamheden: ${d.get('service')}\n\nMijn plannen:\n${d.get('message')}\n\nMet vriendelijke groet,\n${d.get('name')}`;window.location.href=`mailto:info@vanommenschilderwerken.nl?subject=${encodeURIComponent('Aanvraag '+d.get('service')+' — '+d.get('city'))}&body=${encodeURIComponent(body)}`;form.querySelector('.form-status').hidden=false;});
function openDialog(dialog){dialog.showModal();document.body.classList.add('dialog-open');}
// Keep the visitor's filled-in wishes available when email is not configured.
const quoteForm=document.querySelector('#offerte');
const quoteWhatsApp=document.querySelector('#quote-whatsapp');
if(quoteForm&&quoteWhatsApp){
 const updateWhatsApp=()=>{
  const d=new FormData(quoteForm);
  const parts=['Beste Stef, graag bespreek ik mijn schilderwerk.'];
  for(const [key,label] of [['name','Naam'],['city','Woonplaats'],['service','Werkzaamheden'],['message','Mijn wensen']]){
   const value=String(d.get(key)||'').trim();if(value)parts.push(label+': '+value);
  }
  quoteWhatsApp.href='https://wa.me/31624996700?text='+encodeURIComponent(parts.join('\n\n'));
 };
 quoteForm.addEventListener('input',updateWhatsApp);quoteForm.addEventListener('change',updateWhatsApp);quoteWhatsApp.addEventListener('click',updateWhatsApp);
}
document.querySelectorAll('dialog').forEach(dialog=>{dialog.querySelector('.dialog-close').addEventListener('click',()=>dialog.close());dialog.addEventListener('close',()=>document.body.classList.remove('dialog-open'));dialog.addEventListener('click',e=>{if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dialog.close();}});});
document.querySelector('[data-privacy]')?.addEventListener('click',()=>openDialog(document.querySelector('#privacy-dialog')));
const projects = [{"title": "Zorgvuldig voorbereid", "category": "BINNENPROJECT / VOORBEREIDING", "image": "/assets/preparation.jpg", "alt": "Plafond met geplamuurde plekken, voorbereid voor het schilderen", "source": "https://www.facebook.com/photo/?fbid=122111487393222854&set=pb.61586685635291.-2207520000"}, {"title": "Strak in de lak", "category": "BINNENPROJECT / LAKWERK", "image": "/assets/hero.jpg", "alt": "Glanzend wit geschilderd plafond met weerspiegeling van de houten wand", "source": "https://www.facebook.com/photo.php?fbid=122111487507222854&set=pb.61586685635291.-2207520000&type=3"}, {"title": "Een verzorgd geheel", "category": "BINNENPROJECT / AFWERKING", "image": "/assets/detail.jpg", "alt": "Wit afgewerkt plafond boven een zwarte glazen schuifpui", "source": "https://www.facebook.com/photo/?fbid=122111487417222854&set=pb.61586685635291.-2207520000"}];
const grid=document.querySelector('#project-grid');
if(grid) projects.forEach(project=>{const card=document.createElement('button');card.type='button';card.className='project-card';card.setAttribute('aria-label',project.title+' — vergroot de foto');const wrapper=document.createElement('div');wrapper.className='project-image';const img=document.createElement('img');img.src=project.image;img.alt=project.alt;img.loading='lazy';img.width=700;img.height=900;wrapper.append(img);const title=document.createElement('h3');title.textContent=project.title;const subtitle=document.createElement('p');subtitle.textContent=project.category;card.append(wrapper,title,subtitle);card.addEventListener('click',()=>{document.querySelector('#photo-image').src=project.image;document.querySelector('#photo-image').alt=project.alt;document.querySelector('#photo-title').textContent=project.title;document.querySelector('#photo-source').href=project.source;openDialog(document.querySelector('#photo-dialog'));});grid.append(card);});

const selectedService=new URLSearchParams(window.location.search).get('dienst');
const serviceSelect=document.querySelector('[name="service"]');
if(serviceSelect&&selectedService&&Array.from(serviceSelect.options).some(option=>option.value===selectedService)) serviceSelect.value=selectedService;
// Keep bookmarks from the original one-page website useful.
if(document.body.classList.contains('page-home')){
 const formerSections={'#diensten':'/diensten/','#projecten':'/ons-werk/','#over':'/over-stef/','#werkwijze':'/over-stef/#werkwijze','#contact':'/contact/','#offerte':'/contact/#offerte','#vragen':'/contact/#vragen'};
 if(formerSections[window.location.hash])window.location.replace(formerSections[window.location.hash]);
}
// Native buttons support touch, keyboard and screen readers; both images remain visible without JavaScript.
document.querySelectorAll('[data-comparison]').forEach(comparison=>{
 const controls=comparison.querySelector('.comparison-controls');
 const buttons=Array.from(comparison.querySelectorAll('[data-compare-view]'));
 const photos=Array.from(comparison.querySelectorAll('[data-compare-image]'));
 const status=comparison.querySelector('.comparison-status');
 // Schuifregelaar: beide foto's liggen over elkaar. Een native range werkt met
 // muis, touch en toetsenbord; de onzichtbare thumb valt precies op de greep.
 if('slider' in comparison.dataset){
  const images=comparison.querySelector('.comparison-images');
  const range=document.createElement('input');
  range.type='range';range.min='0';range.max='100';range.value='50';range.className='comparison-range';
  range.setAttribute('aria-label','Schuif om de foto voor en na het schilderen te vergelijken');
  const handle=document.createElement('span');
  handle.className='comparison-handle';handle.setAttribute('aria-hidden','true');
  handle.innerHTML='<span class="comparison-knob"><svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 6l-6 6 6 6M15 6l6 6-6 6"/></svg></span>';
  const update=()=>{
   images.style.setProperty('--split',range.value/100);
   range.setAttribute('aria-valuetext',`${range.value}% voor, ${100-range.value}% na`);
  };
  range.addEventListener('input',update);
  images.append(range,handle);
  comparison.classList.add('is-slider');
  update();
  return;
 }
 controls.hidden=false;
 buttons.forEach(button=>button.addEventListener('click',()=>{
  const view=button.dataset.compareView;
  comparison.dataset.view=view;
  buttons.forEach(option=>option.setAttribute('aria-pressed',String(option===button)));
  photos.forEach(photo=>{photo.hidden=view!=='both'&&photo.dataset.compareImage!==view;});
  status.textContent=view==='both'?'Voor en na naast elkaar.':view==='before'?'De foto vóór het schilderen wordt getoond.':'De foto na het schilderen wordt getoond.';
 }));
});

// Privacy-friendly aggregate measurement: no cookies, visitor IDs, local
// storage, referrers, IP addresses or user agents are written by this code.
window.vosTrack=(event,path=location.pathname)=>{
 const body=JSON.stringify({event,path});
 if(navigator.sendBeacon){navigator.sendBeacon('/api/events',new Blob([body],{type:'application/json'}));return;}
 fetch('/api/events',{method:'POST',headers:{'Content-Type':'application/json'},body,keepalive:true}).catch(()=>{});
};
window.vosTrack('page_view');
document.addEventListener('click',event=>{
 const link=event.target.closest('a[href]');if(!link)return;
 const href=link.getAttribute('href')||'';
 if(href.startsWith('tel:'))window.vosTrack('phone_click');
 else if(href.includes('wa.me/'))window.vosTrack('whatsapp_click');
 else if(href.startsWith('/afspraak'))window.vosTrack('appointment_cta');
 else if(href.includes('/contact/')&&href.includes('offerte'))window.vosTrack('quote_cta');
});
if(quoteForm){
 let started=false;
 quoteForm.addEventListener('focusin',()=>{if(!started){started=true;window.vosTrack('quote_start');}});
 quoteForm.addEventListener('submit',()=>window.vosTrack('quote_mail_open'));
}
