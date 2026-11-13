import fs from 'node:fs/promises';
import {Presentation,PresentationFile} from '@oai/artifact-tool';
import {appendSlides} from '../presentation/build_slides.mjs';
const root='C:/Users/siervod/Documents/ChatGPT/USGS catalog statistics';
const spec=JSON.parse(await fs.readFile(root+'/presentation/slide_data.json','utf8'));
const presentation=Presentation.create({slideSize:{width:1280,height:720}});
const cover={title:'U.S. authoritative earthquake networks',paragraphs:['USGS ComCat comparison','11 August–10 November 2026 UTC','25,494 earthquakes across 12 regional networks','Automatic revisions and reviewed phase support'],caption:'Regional ANSS authoritative networks. Worldwide NEIC reporting is excluded.',source:'network_summary.csv'};
await appendSlides({presentation,input:{slides:[cover,...spec.slides],repository:spec.repository}});
await fs.mkdir(root+'/presentation/output',{recursive:true});
const pptx=await PresentationFile.exportPptx(presentation);
await pptx.save(root+'/presentation/output/usgs_authoritative_networks.pptx');
for(let i=0;i<presentation.slides.items.length;i++){
 const png=await presentation.export({slide:presentation.slides.items[i],format:'png',scale:1});
 await fs.writeFile(root+`/build/slide-${i+1}.png`,new Uint8Array(await png.arrayBuffer()));
}
console.log('Exported',presentation.slides.items.length,'slides');
