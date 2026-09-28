import {readFile,writeFile,mkdir,cp,readdir} from 'node:fs/promises';
import path from 'node:path';
const root=process.cwd();
await mkdir('dist/client',{recursive:true});
await mkdir('dist/server',{recursive:true});
await mkdir('dist/.openai',{recursive:true});
for(const entry of await readdir('dist',{withFileTypes:true})){
 if(['client','server','.openai','afspraken-beheer'].includes(entry.name))continue;
 await cp(path.join('dist',entry.name),path.join('dist/client',entry.name),{recursive:true});
}
const admin=await readFile('dist/.openai/admin-page.html','utf8');
const source=await readFile('worker/index.js','utf8');
await cp('worker/confirmation.js','dist/server/confirmation.js');
const seo=await readFile('dist/.openai/seo-runtime.json','utf8');
await writeFile('dist/server/index.js',source.replace('export default createWorker();','export default createWorker('+JSON.stringify(admin)+','+seo+');'));
await cp('.openai/hosting.json','dist/.openai/hosting.json');
await cp('drizzle','dist/.openai/drizzle',{recursive:true});
console.log('Built static client, protected appointment manager and D1 API.');
