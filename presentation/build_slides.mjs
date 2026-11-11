// Reusable Artifact Session callback. Charts are native, editable slide objects.
export async function appendSlides({presentation,input}) {
  const addText=(s,text,x,y,w,h,size,color='#12374A',bold=false)=>{
    const t=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
    t.text=text;t.text.style={fontFamily:'Arial',fontSize:size,color,bold};return t;
  };
  for (const spec of input.slides) {
    const s=presentation.slides.add({width:1280,height:720});s.background.fill='#FFFFFF';
    addText(s,spec.title,60,30,1160,65,34,'#12374A',true);
    if(spec.paragraphs){
      spec.paragraphs.forEach((p,i)=>addText(s,p,76,150+i*105,1110,85,25,'#334155'));
    }
    const charts=spec.charts||[];
    charts.forEach((c,i)=>{
      const single=charts.length===1;
      const x=single?65:55+i*610, w=single?1140:565;
      const line=c.type==='line';
      const config={position:{left:x,top:123,width:w,height:470},title:c.title,
        titleTextStyle:{fontFamily:'Arial',fontSize:21,fill:'#12374A',bold:true},
        categories:c.categories,series:c.series.map(z=>({...z, ...(line?{line:{fill:z.fill,width:2},marker:{symbol:'circle',size:4,fill:z.fill}}:{})})),
        hasLegend:c.series.length>1,
        legend:{position:'bottom',textStyle:{fontFamily:'Arial',fontSize:line?13:16,fill:'#334155'}},
        chartFill:'#FFFFFF',plotAreaFill:'#FFFFFF',chartLine:{fill:'none',width:0},plotAreaLine:{fill:'none',width:0},
        xAxis:{textStyle:{fontFamily:'Arial',fontSize:line?17:16,fill:'#334155'},line:{fill:'#B8C5CB',width:1}},
        yAxis:{textStyle:{fontFamily:'Arial',fontSize:16,fill:'#334155'},numberFormatCode:c.numberFormat,
          majorGridlines:{fill:'#E3E9ED',width:1},...(c.max!==null&&c.max!==undefined?{max:c.max}:{})},
        displayBlanksAs:'gap',
      };
      if(!line){config.barOptions={direction:'bar',grouping:c.stacked?'stacked':'clustered',gapWidth:55};
        config.dataLabels={showValue:c.series.length===1,position:'outEnd',numberFormatCode:c.numberFormat,textStyle:{fontFamily:'Arial',fontSize:14,fill:'#334155'}};}
      else{config.lineOptions={smooth:false};}
      s.charts.add(c.type,config);
    });
    addText(s,spec.caption||'',65,620,1140,66,18,'#475569');
    s.speakerNotes.text=`${spec.notes||''}\nData: ${input.repository}/blob/master/results/${spec.source}\nMethods: ${input.repository}/blob/master/METHODS.md\nPublication figures and quantiles: ${input.repository}/tree/master/figures\nFull per-metric n and missingness are in the source tables. USGS archive snapshot acquired on 11 November 2026.\nUSGS product definitions: https://earthquake.usgs.gov/data/catalog/products.php`;
  }
  return {totalSlides:presentation.slides.items.length,added:input.slides.length};
}
