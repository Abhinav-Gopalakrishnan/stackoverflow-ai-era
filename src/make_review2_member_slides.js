// Build exactly two slides per member from saved result JSON; requires pptxgenjs.
const pptxgen = require('pptxgenjs');
const fs = require('fs');
const path = require('path');
const root = path.resolve(__dirname, '..');
const out = path.join(root, 'reports/review2');
const C = { bg:'101413', panel:'1B2220', teal:'38DDB5', white:'F4F8F6', muted:'AAB9B5' };
function text(s,t,x,y,w,h,extra={}) { s.addText(t,{x,y,w,h,fontFace:'Arial',fontSize:16,color:C.white,margin:0,isTextBox:true,breakLine:false,...extra}); }
function card(s,x,y,w,h) { s.addShape('roundRect',{x,y,w,h,fill:{color:C.panel},line:{color:C.panel,transparency:100},radius:.1}); }
function deck() {let p=new pptxgen();p.layout='LAYOUT_WIDE';p.author='Review 2 project';p.theme={headFontFace:'Arial',bodyFontFace:'Arial',lang:'en-IN'};return p;}
function slide(p,who,title,n) {let s=p.addSlide();s.background={color:C.bg};text(s,who,0.6,.32,12,.24,{fontSize:10,bold:true,color:C.teal});text(s,title,.6,.75,12.1,.72,{fontSize:28,bold:true});text(s,'STACK OVERFLOW IN THE AI ERA / REVIEW 2',.6,7.12,11,.2,{fontSize:9,color:C.muted});text(s,String(n),12.3,7.12,.4,.2,{fontSize:9,color:C.muted});return s;}
function table(s,rows,x,y,w,colW,font=14) {s.addTable(rows,{x,y,w,colW,border:{type:'solid',color:'394541',pt:.6},fill:C.panel,color:C.white,fontFace:'Arial',fontSize:font,margin:.12,rowH:.47,autoFit:false,bold:false});}
async function main() {
 const arg=process.argv.indexOf('--member');
 const member=arg<0?'all':process.argv[arg+1];
 if(!['all','m2','m5'].includes(member))throw new Error('Use --member m2, m5 or all');
 if(member!=='m2') {
 const ts=JSON.parse(fs.readFileSync(path.join(out,'ts/slide_data.json')));
 let p=deck();p.title='Adhikkesh — Review 2 forecasting';
 let s=slide(p,'ADHIKKESH / MEMBER 5','Compare forecasts against baselines at four horizons',1);
 card(s,.6,1.72,5.0,4.88);
 text(s,'DESIGN',.9,1.98,4.3,.3,{fontSize:13,bold:true,color:C.teal});
 text(s,'400 complete weekly observations per series\n\nValidation: July–December 2024\nBacktest: January 2025 onward\n\nExpanding training window; refit every 4 weeks\n\nNaive · seasonal naive · drift\nDamped ETS · SARIMAX',.9,2.5,4.32,3.8,{fontSize:16,paraSpaceAfter:5});
 let a=ts.summary.filter(r=>r.model==='sarimax').sort((x,y)=>x.horizon-y.horizon);
 text(s,'SARIMAX vs naive / matched successful origins',5.98,1.95,6.65,.6,{fontSize:17,bold:true,color:C.teal});
 table(s,[['Weeks','MASE','Skill','95% coverage'],...a.map(r=>[r.horizon,r.mase.toFixed(3),(100*r.skill_vs_naive).toFixed(1)+'%',(100*r.coverage95).toFixed(1)+'%'])],6,2.75,6.68,[1.0,1.4,1.7,2.58],15);
 text(s,'Skill = reduction in scaled error relative to naive.\nMeasured coverage is below the nominal 95%; bands are too narrow.',6,5.6,6.5,.8,{fontSize:15,color:C.muted});
 s.addNotes('I prepared complete weekly counts for all 14 series. Model settings were chosen using 2024 validation data, before the 2025 onward backtest. At each origin the training window expands and the models refit. We evaluate one, four, thirteen and twenty-six weeks ahead, comparing against three simple baselines. This table uses identical successful origins. A higher skill value means lower scaled error than naive. The interval coverage is much lower than its nominal level, which is a limitation we report.');
 s=slide(p,'ADHIKKESH / MEMBER 5','Forecasts extend to February 2027; uncertainty remains',2);
 s.addImage({path:path.join(out,'ts/forecast_ALL.png'),x:.6,y:1.78,w:7.78,h:3.6});
 let q=ts.site;text(s,'SITE TOTAL',8.7,1.95,3.6,.35,{fontSize:13,color:C.teal,bold:true});
 text(s,q.selected_model.toUpperCase(),8.7,2.48,3.7,.45,{fontSize:23,bold:true});
 text(s,Number(q.last_week_count).toFixed(0)+' → '+Number(q.forecast_week26).toFixed(0)+' per week',8.7,3.25,3.8,.6,{fontSize:23,bold:true});
 text(s,Number(q.change_26w_pct).toFixed(1)+'% at week 26',8.7,4.0,3.7,.5,{fontSize:20,color:C.teal,bold:true});
 text(s,'26 weeks: September 1, 2026\nto February 23, 2027',8.7,4.78,3.8,.6,{fontSize:14,color:C.muted});
 const groups=ts.tag_groups;
 text(s,'Steep decline: '+(groups['steep decline']||[]).join(', ')+'\nDeclining: '+(groups['declining']||[]).join(', ')+'\nZero baseline: '+(groups['not classifiable: zero baseline']||[]).join(', ')+' — percentage change undefined.\nThresholds: < −40% steep decline; −40% to −10% declining; > −10% stabilising.',.8,5.66,11.8,1.02,{fontSize:13,color:C.muted});
 s.addNotes('The final model selected from validation is refitted on all 400 weeks. The forecast runs through February 2027, with eighty and ninety-five percent intervals. The point forecast is the back-transformed median. We classify tag changes by fixed thresholds; a zero initial count cannot support a percentage change. We will combine these forecasts with Akshay’s structural-break findings. These are uncertain projections and their association with AI adoption does not establish cause.');
 await p.writeFile({fileName:path.join(out,'member5_review2_slides.pptx')});
 }
 if(member!=='m5') {
 const m=JSON.parse(fs.readFileSync(path.join(out,'text/slide_data.json')));
 let p=deck();p.title='Rishiikesh — Review 2 text preparation, tone and complexity';
 let s=slide(p,'RISHIIKESH / MEMBER 2','Prepare prose for topics; retain code for complexity',1);
 card(s,.6,1.72,7.02,4.88);text(s,'TEXT PREPARATION',.9,2.0,6.2,.3,{fontSize:13,color:C.teal,bold:true});
 text(s,'Title + prose → unescape HTML\n\nProtect c++, c#, .net and framework tokens\n\nReplace URLs, paths and long numbers\n\nspaCy lemmatisation + written stopword list\n\nKeep question IDs, periods and sampling weights',.9,2.52,6.1,3.65,{fontSize:17});
 card(s,7.88,1.72,4.85,4.88);
 for(const [i,num,label] of [[0,m.stats.documents_after,'documents retained'],[1,m.stats.vocabulary_size,'distinct terms'],[2,m.stats.empty_after_cleaning,'empty after cleaning']]) {
  text(s,Number(num).toLocaleString('en-IN'),8.2,2.05+i*1.32,4.2,.5,{fontSize:29,bold:true,color:C.teal});text(s,label,8.2,2.67+i*1.32,4.15,.3,{fontSize:15,color:C.muted});
 }
 s.addNotes('I prepared the corpus from titles and prose with code removed. HTML entities are decoded and technology names are protected before punctuation is stripped. The text is lemmatised using spaCy with a written stopword list. Code is excluded from topics and tone but measured separately for complexity. The corpus retains identifiers, periods and sampling weights so Nishanth can calculate weighted topic trends and join the outcome metadata. Empty documents are counted explicitly.');
 s=slide(p,'RISHIIKESH / MEMBER 2','Questions became longer; VADER agrees poorly with a human',2);
 const get=name=>m.complexity.find(r=>r.metric===name);
 const prose=get('prose_words'), code=get('code_lines');
 s.addChart(p.ChartType.bar,[{name:'Pre',labels:['Prose words','Code lines'],values:[prose.pre,code.pre]},{name:'Post',labels:['Prose words','Code lines'],values:[prose.post,code.post]}],{x:.6,y:1.82,w:6.7,h:3.82,barDir:'col',catAxisLabelColor:C.white,valAxisLabelColor:C.muted,chartColors:['7EAAA0',C.teal],showLegend:true,legendColor:C.white,showValue:true,dataLabelColor:C.white,dataLabelPosition:'outEnd',showTitle:false,valAxisMinVal:0,showCatName:false,showBorder:false,showCatName:false,chartArea:{fill:{color:C.bg}},plotArea:{fill:{color:C.bg}},valGridLine:{color:'394541',width:.5},catGridLine:{style:'none'},fontFace:'Arial',showSerName:false});
 text(s,'Weighted medians; transition months excluded',.8,5.86,6.4,.45,{fontSize:13,color:C.muted});
 const fr=m.tone.find(r=>r.measure==='frustration');
 card(s,7.72,1.82,5.0,4.8);text(s,'PRE → POST',8.04,2.12,4.2,.3,{fontSize:13,bold:true,color:C.teal});
 text(s,'Prose-word change: +'+prose.change+'\n95% interval ['+prose.lower95+', '+prose.upper95+']',8.04,2.72,4.18,.85,{fontSize:19,bold:true});
 text(s,'Frustration-phrase flag:\n'+(100*fr.pre).toFixed(1)+'% → '+(100*fr.post).toFixed(1)+'%',8.04,3.91,4.16,.78,{fontSize:18});
 const v=m.validation;
 const validation=v.accuracy==null?'Human reference incomplete; metrics unavailable.':
  'VADER vs 200 M3 human labels: '+(100*v.accuracy).toFixed(1)+'% accuracy; macro-F1 '+v.macro_f1.toFixed(3)+'.\n'+
  (v.ai_human_kappa==null?'Two-human validation complete.':'Human–AI κ '+v.ai_human_kappa.toFixed(3)+'. Two-human validation remains incomplete.');
 text(s,validation,8.04,5.06,4.16,1.22,{fontSize:13,color:C.muted});
 s.addNotes('The comparisons use sampling weights and exclude transition months. Median prose length and code lines increased, with one thousand bootstrap resamples. '+validation+' The AI annotations were created by Codex, not by a second human. They are not adjudicated gold labels. Use the frustration-phrase flag as the primary exploratory tone proxy, with no claim that the flag measures verified emotion.');
 await p.writeFile({fileName:path.join(out,'member2_review2_slides.pptx')});
 }
}
main().catch(e=>{console.error(e);process.exit(1)});
