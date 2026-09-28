import test from 'node:test';
import assert from 'node:assert/strict';
import {createWorker} from '../worker/index.js';
const worker=createWorker('',{routes:['/','/diensten/','/diensten/binnenschilderwerk/']});
const env={ASSETS:{fetch:async()=>new Response('asset',{headers:{'Content-Type':'text/html'}})}};
test('HTTP and duplicate page URLs redirect without dropping query strings',async()=>{
 for(const [input,target] of [
  ['http://example.test/Diensten/index.html?dienst=binnen','https://example.test/diensten/?dienst=binnen'],
  ['https://example.test/diensten','https://example.test/diensten/'],
  ['https://example.test/diensten/binnenschilderwerk.html','https://example.test/diensten/binnenschilderwerk/'],
  ['https://example.test/index.html','https://example.test/']]){
  const response=await worker.fetch(new Request(input),env);
  assert.equal(response.status,308);assert.equal(response.headers.get('location'),target);
 }
});
test('canonical pages have HTTPS headers and remain indexable; protected manager stays protected',async()=>{
 const response=await worker.fetch(new Request('https://example.test/diensten/'),env);
 assert.equal(response.status,200);assert.match(response.headers.get('strict-transport-security'),/31536000/);
 assert.equal(response.headers.get('x-robots-tag'),null);
 const admin=await worker.fetch(new Request('https://example.test/afspraken-beheer/'),env);
 assert.equal(admin.status,403);assert.equal(admin.headers.get('x-robots-tag'),'noindex');
});
test('machine-readable resources return appropriate content types',async()=>{
 for(const [path,type] of [['/llms.txt','text/plain'],['/robots.txt','text/plain'],['/sitemap.xml','application/xml']]){
  const response=await worker.fetch(new Request('https://example.test'+path),env);
  assert.ok(response.headers.get('content-type').startsWith(type));
 }
});
test('unknown pages return the custom 404 with noindex headers',async()=>{
 const fallbackWorker=createWorker('',{routes:['/','/404/']});
 const fallbackEnv={ASSETS:{fetch:async request=>new URL(request.url).pathname==='/404/'?new Response('<h1>Hier hoeft geen verf overheen.</h1>',{headers:{'Content-Type':'text/html'}}):new Response('missing',{status:404})}};
 const response=await fallbackWorker.fetch(new Request('https://example.test/bestaat-niet/'),fallbackEnv);
 assert.equal(response.status,404);assert.equal(response.headers.get('x-robots-tag'),'noindex, nofollow');assert.match(await response.text(),/Hier hoeft geen verf overheen/);
});
