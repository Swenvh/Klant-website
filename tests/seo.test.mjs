// Controles op de statische build voor Cloudflare Pages: headers, 404, sitemap en robots.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
const read=p=>readFileSync(new URL('../dist/'+p,import.meta.url),'utf8');

test('_headers zet beveiligingsheaders, cache en content-types',()=>{
 const headers=read('_headers');
 for(const h of ['Strict-Transport-Security','X-Content-Type-Options: nosniff','Referrer-Policy','Permissions-Policy','X-Frame-Options','Content-Security-Policy'])assert.match(headers,new RegExp(h));
 assert.match(headers,/\/assets\/\*\n\s+Cache-Control: public, max-age=604800/);
 assert.match(headers,/\/llms\.txt\n\s+Content-Type: text\/plain/);
 assert.match(headers,/\/sitemap\.xml\n\s+Content-Type: application\/xml/);
 assert.match(headers,/script-src 'self' https:\/\/challenges\.cloudflare\.com/);
});
test('404.html bestaat voor Pages, is noindex en gelijk aan /404/',()=>{
 assert.ok(existsSync(new URL('../dist/404.html',import.meta.url)));
 assert.match(read('404.html'),/noindex/);
 assert.equal(read('404.html'),read('404/index.html'));
});
test('sitemap bevat geen noindex-pagina’s en robots verwijst naar de sitemap',()=>{
 const sitemap=read('sitemap.xml');
 for(const p of ['/404/','/bedankt/'])assert.doesNotMatch(sitemap,new RegExp(p.replace('/','\\/')));
 assert.match(read('robots.txt'),/Sitemap: https:\/\/.+\/sitemap\.xml/);
 for(const bot of ['GPTBot','ClaudeBot','PerplexityBot','Google-Extended'])assert.match(read('robots.txt'),new RegExp('User-agent: '+bot+'\\nAllow: /'));
});
test('het formulier wijst naar de Pages Function en de functie bestaat',()=>{
 assert.match(read('offerte/index.html'),/<form id="offerte"[^>]*action="\/api\/offerte"/);
 assert.ok(existsSync(new URL('../functions/api/offerte.js',import.meta.url)));
 assert.ok(existsSync(new URL('../functions/api/events.js',import.meta.url)));
});
