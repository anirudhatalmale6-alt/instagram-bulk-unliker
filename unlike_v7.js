(async()=>{
const D=ms=>new Promise(r=>setTimeout(r,ms));
const csrf=(document.cookie.match(/csrftoken=([^;]+)/)||[])[1]||'';

function rClick(el){
el.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,cancelable:true,view:window}));
el.dispatchEvent(new PointerEvent('pointerup',{bubbles:true,cancelable:true,view:window}));
el.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,view:window}));
}

console.log('=== Instagram Bulk Unliker v7 ===');

// PHASE 1: Try API
console.log('Trying API approach...');
try{
let res=await fetch('/api/v1/feed/liked/?count=20',{headers:{'X-IG-App-ID':'936619743392459'},credentials:'include'});
if(res.ok){
let data=await res.json();
let items=data.items||[];
if(items.length>0){
console.log('API works! Found '+items.length+' liked posts.');
let t=0,maxId='';
while(true){
let url='/api/v1/feed/liked/?count=50'+(maxId?'&max_id='+maxId:'');
let r2=await fetch(url,{headers:{'X-IG-App-ID':'936619743392459'},credentials:'include'});
if(!r2.ok)break;
let d2=await r2.json();
let batch=d2.items||[];
if(!batch.length)break;
for(let item of batch){
let id=item.pk||item.id||(item.media&&item.media.pk);
if(!id)continue;
let ur=await fetch('/api/v1/web/likes/'+id+'/unlike/',{method:'POST',headers:{'X-CSRFToken':csrf,'X-IG-App-ID':'936619743392459','Content-Type':'application/x-www-form-urlencoded'},credentials:'include'});
if(ur.ok){t++;if(t%10===0)console.log('Unliked '+t+'...');}
else if(ur.status===429){console.log('Rate limited at '+t+'. Wait 3 min then run again.');return;}
await D(1500);
}
maxId=d2.next_max_id||'';
if(!d2.more_available)break;
await D(2000);
}
console.log('DONE via API! Unliked '+t+' posts.');
alert('Done! Unliked '+t+' posts. Run again to check for more.');
return;
}else{
console.log('API returned no items. Trying UI approach...');
}
}else{
console.log('API status '+res.status+'. Trying UI approach...');
}
}catch(e){console.log('API error: '+e.message+'. Trying UI...');}

// PHASE 2: UI approach
console.log('=== UI Approach ===');
if(!location.href.includes('your_activity/interactions/likes')){
location.href='/your_activity/interactions/likes';
console.log('Navigating to Likes page. Run script again after page loads.');
return;
}

let total=0;
for(let round=0;round<30;round++){
await D(2000);

let sel=[...document.querySelectorAll('span')].find(e=>e.textContent.trim()==='Select'&&!e.children.length&&e.offsetParent);
if(!sel)sel=[...document.querySelectorAll('div,button')].find(e=>e.textContent.trim()==='Select'&&e.offsetParent&&(!e.children.length||(e.children.length===1&&e.children[0].nodeType===3)));
if(!sel){console.log('No Select button. Total unliked: '+total);alert('Done! Unliked '+total+' items.');break;}

rClick(sel);
console.log('Round '+(round+1)+': Clicked Select');
await D(2500);

let gridItems=[];

// Method A: role=button elements that are grid-sized
document.querySelectorAll('[role="button"],[tabindex="0"]').forEach(el=>{
let r=el.getBoundingClientRect();
if(r.width>80&&r.height>80&&r.width<350&&r.height<350&&r.top>150){
gridItems.push(el);
}
});

// Method B: divs containing img, video, or "Failed to load" text
if(gridItems.length<3){
gridItems=[];
document.querySelectorAll('div').forEach(el=>{
if(el.children.length>10)return;
let r=el.getBoundingClientRect();
if(r.width>80&&r.width<350&&r.height>80&&r.height<350&&r.top>150){
if(el.querySelector('img,video')||el.textContent.includes('Failed to load')){
gridItems.push(el);
}
}
});
}

// Method C: find rows of same-sized siblings
if(gridItems.length<3){
gridItems=[];
document.querySelectorAll('div').forEach(parent=>{
let ch=[...parent.children];
if(ch.length>=2&&ch.length<=5){
let rects=ch.map(c=>c.getBoundingClientRect());
let allSimilar=rects.every(r=>r.width>80&&r.height>80&&Math.abs(r.width-rects[0].width)<20);
if(allSimilar&&rects[0].top>150){
gridItems.push(...ch);
}
}
});
}

// Deduplicate: keep innermost elements, remove overlapping
gridItems=gridItems.filter((a,i)=>!gridItems.some((b,j)=>i!==j&&a!==b&&a.contains(b)));
let unique=[];
for(let g of gridItems){
let r=g.getBoundingClientRect();
if(!unique.some(u=>{let ur=u.getBoundingClientRect();return Math.abs(ur.left-r.left)<15&&Math.abs(ur.top-r.top)<15;})){
unique.push(g);
}
}
gridItems=unique;

console.log('Found '+gridItems.length+' grid items');

if(gridItems.length===0){
console.log('No grid items found. Total: '+total);
alert('Could not find items to select. Total unliked: '+total);
break;
}

let clicked=0;
for(let item of gridItems.slice(0,50)){
rClick(item);
clicked++;
await D(350);
}
console.log('Clicked '+clicked+' items');
await D(2000);

let unlikeBtn=[...document.querySelectorAll('button,div[role="button"]')].find(e=>e.textContent.trim()==='Unlike'&&e.offsetParent);
if(!unlikeBtn){
console.log('Unlike button not found. Selection may not have registered.');
console.log('Trying to scroll and look again...');
window.scrollTo(0,document.body.scrollHeight);
await D(1000);
unlikeBtn=[...document.querySelectorAll('button,div[role="button"]')].find(e=>e.textContent.trim()==='Unlike'&&e.offsetParent);
}

if(!unlikeBtn){
console.log('Still no Unlike button. Total: '+total);
alert('Unlike button did not appear after selecting items. The selection clicks may not be registering. Total unliked: '+total);
break;
}

rClick(unlikeBtn);
console.log('Clicked Unlike');
await D(2500);

let confirmBtn=[...document.querySelectorAll('button')].find(e=>e.textContent.trim()==='Unlike'&&e.offsetParent);
if(confirmBtn&&confirmBtn!==unlikeBtn){
rClick(confirmBtn);
await D(2000);
}

total+=clicked;
console.log('Batch done! Total unliked: '+total);
await D(3000);
location.reload();
await D(6000);
}
console.log('FINISHED. Total unliked: '+total);
})();