const menuButton = document.querySelector('.menu-toggle');
const mobileNav = document.querySelector('#mobile-nav');
function closeMenu(){menuButton.setAttribute('aria-expanded','false');menuButton.setAttribute('aria-label','Menu openen');mobileNav.hidden=true;}
menuButton.addEventListener('click',()=>{const opened=menuButton.getAttribute('aria-expanded')==='true';menuButton.setAttribute('aria-expanded',String(!opened));menuButton.setAttribute('aria-label',opened?'Menu openen':'Menu sluiten');mobileNav.hidden=opened;});
mobileNav.querySelectorAll('a').forEach(a=>a.addEventListener('click',closeMenu));
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!mobileNav.hidden){closeMenu();menuButton.focus();}});
window.matchMedia('(min-width:851px)').addEventListener('change',e=>{if(e.matches)closeMenu();});
// Uitklapbaar dienstenmenu: met de muis opent het via CSS; de knop werkt voor touch, toetsenbord en schermlezers.
document.querySelectorAll('.nav-dropdown').forEach(drop=>{
 const toggle=drop.querySelector('.nav-dropdown-toggle');
 const set=open=>{drop.classList.toggle('is-open',open);toggle.setAttribute('aria-expanded',String(open));};
 toggle.addEventListener('click',()=>set(toggle.getAttribute('aria-expanded')!=='true'));
 drop.addEventListener('keydown',e=>{if(e.key==='Escape'&&drop.classList.contains('is-open')){e.stopPropagation();set(false);toggle.focus();}});
 document.addEventListener('click',e=>{if(!drop.contains(e.target))set(false);});
});

document.querySelector('#offerte')?.addEventListener('submit',async e=>{
 e.preventDefault();const form=e.currentTarget;if(!form.reportValidity())return;
 const status=form.querySelector('.form-status'),button=form.querySelector('button[type=submit]');
 const say=(text,error)=>{status.hidden=false;status.textContent=text;status.classList.toggle('is-error',!!error);};
 const data=new FormData(form);
 form.dataset.requestKey||=crypto.randomUUID();data.set('requestKey',form.dataset.requestKey);
 button.disabled=true;say('Bezig met versturen…');
 try{
  const response=await fetch('/api/offerte',{method:'POST',body:data,headers:{Accept:'application/json'}});
  const result=await response.json().catch(()=>({}));
  if(response.ok){window.vosTrack?.('quote_sent');window.location.href='/bedankt/offerte/';return;}
  say(result.error||'Versturen lukt op dit moment niet. Probeer het opnieuw of bel 06 24 99 67 00.',true);
 }catch{say('Versturen lukt op dit moment niet. Controleer uw verbinding, probeer het opnieuw of bel 06 24 99 67 00.',true);}
 button.disabled=false;
});
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
const projects = [{"title": "Zorgvuldig voorbereid", "category": "BINNENPROJECT / VOORBEREIDING", "image": "/assets/preparation.jpg", "alt": "Plafond met geplamuurde plekken, voorbereid voor het schilderen", "source": "https://www.facebook.com/photo/?fbid=122111487393222854&set=pb.61586685635291.-2207520000"}, {"title": "Strak in de lak", "category": "BINNENPROJECT / EINDRESULTAAT", "image": "/assets/hero.jpg", "alt": "Glanzend wit geschilderd plafond met weerspiegeling van de houten wand", "source": "https://www.facebook.com/photo.php?fbid=122111487507222854&set=pb.61586685635291.-2207520000&type=3"}, {"title": "Een verzorgd geheel", "category": "BINNENPROJECT / AFWERKING", "image": "/assets/detail.jpg", "alt": "Wit afgewerkt plafond boven een zwarte glazen schuifpui", "source": "https://www.facebook.com/photo/?fbid=122111487417222854&set=pb.61586685635291.-2207520000"}];
// Responsive varianten (gemaakt door scripts/optimize-assets.py); kaarten laden een kleine versie, de fotoviewer de grote.
const projectVariants={'/assets/preparation.jpg':[480,960,1440,1536],'/assets/hero.jpg':[480,960,1440,1920,2048],'/assets/detail.jpg':[480,960,1440,1536],'/assets/behangwerk-aan-het-werk.jpg':[480,960,1086]};
const variantUrl=(image,width)=>image.replace(/\.[a-z]+$/i,'')+'-responsive-'+width+'.webp';
const variantSrcset=image=>(projectVariants[image]||[]).map(w=>variantUrl(image,w)+' '+w+'w').join(', ');
const largestVariant=(image,max)=>{const ws=(projectVariants[image]||[]).filter(w=>w<=max);return ws.length?variantUrl(image,ws[ws.length-1]):image;};
const grid=document.querySelector('#project-grid');
if(grid) projects.forEach(project=>{const card=document.createElement('button');card.type='button';card.className='project-card';card.setAttribute('aria-label',project.title+' — vergroot de foto');const wrapper=document.createElement('div');wrapper.className='project-image';const img=document.createElement('img');img.src=largestVariant(project.image,960);img.srcset=variantSrcset(project.image);img.sizes='(max-width: 700px) 100vw, 33vw';img.alt=project.alt;img.loading='lazy';img.width=700;img.height=900;wrapper.append(img);const title=document.createElement('h3');title.textContent=project.title;const subtitle=document.createElement('p');subtitle.textContent=project.category;card.append(wrapper,title,subtitle);card.addEventListener('click',()=>{document.querySelector('#photo-image').src=largestVariant(project.image,1920);document.querySelector('#photo-image').alt=project.alt;document.querySelector('#photo-title').textContent=project.title;document.querySelector('#photo-source').href=project.source;openDialog(document.querySelector('#photo-dialog'));});grid.append(card);});

const selectedService=new URLSearchParams(window.location.search).get('dienst');
const serviceRadio=selectedService&&Array.from(document.querySelectorAll('input[name="service"]')).find(r=>r.value===selectedService);
if(serviceRadio){serviceRadio.checked=true;if(selectedService.startsWith('Zakelijk')){const z=document.querySelector('input[name="type"][value="Zakelijk"]');if(z)z.checked=true;}}
// Keep bookmarks from the original one-page website useful.
if(document.body.classList.contains('page-home')){
 const formerSections={'#diensten':'/diensten/','#projecten':'/projecten/','#over':'/over-ons/','#werkwijze':'/over-ons/#werkwijze','#contact':'/contact/','#offerte':'/offerte/'};
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
 if(!controls)return;
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
 quoteForm.addEventListener('submit',()=>window.vosTrack('quote_sent'));
}

// Sticky header: schaduw zodra de bezoeker scrolt.
const stickyHeader=document.querySelector('.header');
if(stickyHeader){const markScrolled=()=>stickyHeader.classList.toggle('is-scrolled',window.scrollY>8);markScrolled();window.addEventListener('scroll',markScrolled,{passive:true});}

// Projectenpagina: een kaart met data-photo opent de fotoviewer met de grote variant.
document.querySelectorAll('.project-kaart[data-photo]').forEach(card=>card.addEventListener('click',()=>{
 const dialog=document.querySelector('#photo-dialog');if(!dialog)return;
 const image=dialog.querySelector('#photo-image');image.src=largestVariant(card.dataset.photo,1920);image.alt=card.querySelector('img')?.alt||'';
 const title=dialog.querySelector('#photo-title');if(title)title.textContent=card.dataset.title||'Project';
 const source=dialog.querySelector('#photo-source');if(source)source.hidden=true;
 openDialog(dialog);
}));

// Projectcarrousel op de plaatspagina's: pijlen schuiven één kaart; swipen werkt via scroll-snap.
document.querySelectorAll('.plaats-projecten').forEach(section=>{
 const strip=section.querySelector('.carrousel');if(!strip)return;
 const knoppen=section.querySelectorAll('.carrousel-knop');
 const stap=()=>{const li=strip.querySelector('li');return li?li.getBoundingClientRect().width+parseFloat(getComputedStyle(strip).columnGap||getComputedStyle(strip).gap||0):strip.clientWidth;};
 const update=()=>{const max=strip.scrollWidth-strip.clientWidth-1;knoppen[0].disabled=strip.scrollLeft<=0;knoppen[1].disabled=strip.scrollLeft>=max;};
 knoppen.forEach(k=>k.addEventListener('click',()=>strip.scrollBy({left:stap()*Number(k.dataset.richting),behavior:'smooth'})));
 strip.addEventListener('scroll',update,{passive:true});window.addEventListener('resize',update);update();
});


// Infaden bij scrollen (2026-11-24): blokken komen 20px van onder in beeld, één keer. Buren krijgen een kleine vertraging na elkaar.
(()=>{
 if(matchMedia('(prefers-reduced-motion: reduce)').matches)return;
 const sel='.home-services .section-heading,.service-tile,.home-intro>*,.werkgebied>*,.projecten-balk>*,.steps article,.page-cta>*,.dienst-intro>*,.dienst-band>*,.dienst-donker>*,.dienst-plaatsen,.local-story article>*,.local-story figure,.plaats-projecten-kop>*,.carrousel>li,.project-kaart,.projecten-intro>*,.project-galerij>*,.project-voorna>*,.about-copy,.about-image,.contact>*,.direct-contact>*,.contact-extra>*,.quote-form,.offerte-side>*,.legal-page>*,.sitemap-lijst>*,.services-overview>*';
 const items=[...document.querySelectorAll(sel)].filter(el=>!el.closest('.hero,.header,.page-intro,.footer')&&!(el.matches('.project-kaart')&&el.closest('.carrousel')));
 if(!items.length)return;
 items.forEach(el=>{const i=[...el.parentElement.children].indexOf(el);el.style.transitionDelay=Math.min(i,5)*90+'ms';el.classList.add('infade');});
 const io=new IntersectionObserver(entries=>entries.forEach(e=>{if(e.isIntersecting){e.target.classList.add('is-in');io.unobserve(e.target);}}),{rootMargin:'0px 0px -8% 0px',threshold:.1});
 items.forEach(el=>io.observe(el));
 // Wat al in beeld staat bij het laden, direct tonen zonder vertraging.
 requestAnimationFrame(()=>items.forEach(el=>{const r=el.getBoundingClientRect();if(r.top<innerHeight*.9&&r.bottom>0){el.style.transitionDelay='0ms';el.classList.add('is-in');io.unobserve(el);}}));
})();
// Keuzeknoppen in het offerteformulier: nog een keer tikken op de gekozen optie maakt de keuze weer ongedaan.
(()=>{
 const labels=document.querySelectorAll('label.keuze');
 if(!labels.length)return;
 labels.forEach(l=>{
  const r=l.querySelector('input[type=radio]');if(!r)return;
  l.addEventListener('pointerdown',()=>{r.dataset.was=r.checked?'1':'';});
  r.addEventListener('click',()=>{if(r.dataset.was==='1'){r.checked=false;r.dataset.was='';r.dispatchEvent(new Event('change',{bubbles:true}));}});
 });
})();
