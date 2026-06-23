// ===== إعدادات الاتصال بالباكند =====
// عند النشر على Render، عدّل DEFAULT_API_URL إلى رابط الـ Backend الخاص بك:
// مثال: "https://qu-assistant-api.onrender.com"
const DEFAULT_API_URL = "https://qu-assistant.onrender.com";
let API='',dept='all',lvl='all',busy=false;
let stats={q:0,helpful:0,notHelpful:0,oos:0};

document.getElementById('bgDiv').style.backgroundImage="url('data:image/png;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/4gHYSUNDX1BST0ZJTEUAAQEAAAHIAAAAAAQwAABtbnRyUkdCIFhZWiAH4AABAAEAAAAAAABhY3NwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQAA9tYAAQAAAADTLQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAlkZXNjAAAA8AAAACRyWFlaAAABFAAAABRnWFlaAAABKAAAABRiWFlaAAABPAAAABR3dHB0AAABUAAAABRyVFJDAAABZAAAAChnVFJDAAABZAAAAChiVFJDAAABZAAAAChjcHJ0AAABjAAAADxtbHVjAAAAAAAAAAEAAAAMZW5VUwAAAAgAAAAcAHMAUgBHAEJYWVogAAAAAAAAb6IAADj1AAADkFhZWiAAAAAAAABimQAAt4UAABjaWFlaIAAAAAAAACSgAAAPhAAAts9YWVogAAAAAAAA9tYAAQAAAADTLXBhcmEAAAAAAAQAAAACZmYAAPKnAAANWQAAE9AAAApbAAAAAAAAAABtbHVjAAAAAAAAAAEAAAAMZW5VUwAAACAAAAAcAEcAbwBvAGcAbABlACAASQBuAGMALgAgADIAMAAxADb/2wBDAAUDBAQEAwUEBAQFBQUGBwwIBwcHBw8LCwkMEQ8SEhEPERETFhwXExQaFRERGCEYGh0dHx8fExciJCIeJBweHx7/2wBDAQUFBQcGBw4ICA4eFBEUHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh7/wAARCALQBQADASIAAhEBAxEB/8QAHAAAAgIDAQEAAAAAAAAAAAAABQYEBwECAwAI/8QAVxAAAQMDAgMFBAYGBgcIAAENAgEDBAAFEQYSEyExByIyQVEUQmFxI1JigZGhFXKCkrHBFjOissLRCCRDU+Hw8Rc0RFSDk9LiJTVFY3MmVXSjJzaEs8P/xAAaAQADAQEBAQAAAAAAAAAAAAABAgMABAUG/8QANhEAAgIBAwQBAwMEAgEEAgMAAAECEQMEEjETIUFRFAUiMkJSYSNxkaEVgWIzsdHhBlMkwfD/2gAMAwEAAhEDEQA/AP...')";

window.onload=()=>{
  API = DEFAULT_API_URL;
  try { localStorage.setItem('api_url', API); } catch(e) {}

  fetch(API+'/health').then(r=>r.json()).then(d=>{
    if(d && d.status==='ok'){
      const dot=document.getElementById('sdot');
      const txt=document.getElementById('stxt');
      if(dot) dot.classList.add('on');
      if(txt) txt.textContent='متصل ✓';
    }
  }).catch(()=>{});

  ['dF','lF'].forEach((id,i)=>{
    const el=document.getElementById(id);
    if(!el) return;
    el.addEventListener('click',e=>{
      if(!e.target.classList.contains('fp')) return;
      document.querySelectorAll('#'+id+' .fp').forEach(p=>p.classList.remove('active'));
      e.target.classList.add('active');
      if(i===0) dept=e.target.dataset.v; else lvl=e.target.dataset.v;
    });
  });
};

function updateStats(){}

async function connect(){ /* لم تعد مستخدمة */ }

async function send(){
  const q=document.getElementById('q').value.trim();
  if(!q||busy) return;
  if(!API){
    toast('⚙️ يجب الاتصال بالـ API أولاً! اضغط على ⚙️ في الأسفل');
    return;
  }
  busy=true; document.getElementById('sb').disabled=true;
  document.getElementById('wlc').style.display='none';
  document.querySelector('.bchips').style.display='none';
  const ca=document.getElementById('ca');
  ca.style.display='flex'; ca.style.flexDirection='column';
  const uw=document.createElement('div'); uw.className='mr user';
  uw.innerHTML='<div class="bub-user">'+esc(q).replace(/\n/g,'<br>')+'</div>';
  ca.appendChild(uw); ca.scrollTop=ca.scrollHeight;
  document.getElementById('q').value='';
  document.getElementById('q').style.height='auto';
  stats.q++; updateStats();
  const tid='ty'+Date.now();
  const tw=document.createElement('div'); tw.className='mr bot'; tw.id=tid;
  tw.innerHTML='<div class="typing-wrap"><div class="typing"><span></span><span></span><span></span></div></div>';
  ca.appendChild(tw); ca.scrollTop=ca.scrollHeight;
  try{
    const res=await fetch(API+'/ask',{
      method:'POST',
      headers:{'Content-Type':'application/json','ngrok-skip-browser-warning':'true'},
      body:JSON.stringify({question:q,department:dept==='all'?null:dept,level:lvl==='all'?null:lvl})
    });
    if(!res.ok) throw new Error('HTTP '+res.status);
    const d=await res.json();
    document.getElementById(tid)?.remove();
    const isOOS=d.answer&&(d.answer.includes('could not find')||d.answer.includes('لم أجد')||d.answer.includes('not available')||d.answer.includes('غير متاح')||d.confidence==='low');
    if(isOOS){addOOS(d.answer);stats.oos++;updateStats();}
    else{addBotCard(q,d);}
  }catch(e){
    document.getElementById(tid)?.remove();
    addOOS('⚠️ حدث خطأ في الاتصال. تأكد من:\n• أن Colab شغال\n• أن URL صحيح\n• اتصال الإنترنت');
  }
  busy=false; document.getElementById('sb').disabled=false;
}

function addBotCard(question,d){
  const ca=document.getElementById('ca');
  const c=d.confidence||'medium';
  const confLabel=c==='high'?'✓ موثّق بدقة عالية':c==='medium'?'~ موثّق':'⚠ ثقة منخفضة';
  const msgId='msg_'+Date.now();

  const sentences=d.answer.split(/(?<=[.!?؟])\s+/);
  const synthText=sentences.slice(0,Math.min(2,sentences.length)).join(' ');
  const fullText=d.answer;
  const hasDetails=fullText.length>synthText.length||d.excerpt;

  const sources=d.sources||[];
  const srcHtml=sources.slice(0,3).map(s=>{
    const name=s.source.replace('.pdf','').replace(/-/g,' ').replace(/_/g,' ');
    const page=s.page?'· ص'+s.page:'';
    const section=s.section?'· '+s.section:'';
    const excerpt=esc(s.excerpt||d.excerpt||synthText).replace(/'/g,"\\'");
    const srcName=esc(s.source).replace(/'/g,"\\'");
    const pageNum=s.page||1;
    return `<a class="src-tag" href="#" onclick="openSourceViewer('${srcName}','${pageNum}','${excerpt}');return false;">📄 ${esc(name)}${page}${section}</a>`;
  }).join('');

  const detailsId='det_'+msgId;
  const detailsBtnHtml=hasDetails?`<button class="details-btn" onclick="toggleDetails('${detailsId}',this)">📖 للتفاصيل اضغط هنا</button>`:'';

  const detailsSectionHtml=hasDetails?
    `<div class="details-section" id="${detailsId}">
      <div>${esc(fullText).replace(/\n/g,'<br>')}</div>
      ${d.excerpt?`<div style="margin-top:10px;padding:8px 12px;background:rgba(200,151,58,0.08);border-right:3px solid var(--gold);border-radius:4px;font-style:italic;font-size:12.5px;color:var(--sub)">${esc(d.excerpt).replace(/\n/g,'<br>')}</div>`:''}
    </div>`:'';

  const w=document.createElement('div'); w.className='mr bot'; w.id=msgId;
  w.innerHTML=
    '<div class="bot-card">'+
      '<div class="synth">'+
        '<div class="synth-label">✨ الإجابة</div>'+
        '<div class="synth-text">'+esc(synthText).replace(/\n/g,'<br>')+'</div>'+
      '</div>'+
      detailsBtnHtml+
      detailsSectionHtml+
      '<div class="src-row">'+srcHtml+'<span class="conf-tag '+c+'">'+confLabel+'</span></div>'+
      '<div class="fb-row" id="fb_'+msgId+'">'+
        '<span class="fb-lbl">هل كانت الإجابة مفيدة؟</span>'+
        '<button class="fb-btn helpful" onclick="feedback(\''+msgId+'\',true)">👍 مفيدة</button>'+
        '<button class="fb-btn nothelpful" onclick="feedback(\''+msgId+'\',false)">👎 غير مفيدة</button>'+
      '</div>'+
    '</div>';
  ca.appendChild(w); ca.scrollTop=ca.scrollHeight;
}

function toggleDetails(id,btn){
  const el=document.getElementById(id);
  if(!el) return;
  const open=el.classList.toggle('open');
  btn.textContent=open?'🔼 إخفاء التفاصيل':'📖 للتفاصيل اضغط هنا';
}

// ===== Google Drive File ID Map =====
const DRIVE_MAP = {
  '1-1-1-12-Academic-Program-Handbook-for-Faculty-Members_17_01.pdf': '1WcE2YiWzBmVG98_kIOCUo8Rh2zWDKvQh',
  '1-1-1-13-Student-Handbook (1).pdf': '1VDGBdoZnWfT2GZslNCrJoLnmG6aH9FwN',
  '1-1-1-15-Organizational-and-Procedural-Guide-for-Administrative-Tasks-in-the-Departments-of-the-College-of-Computer.pdf': '1srisVUNcfmW8K3GeVQjQzJX74bjcsMfb',
  '1-2-1-2-Quality_Manual_Managment_System.pdf': '18R4SFQued3WyO-06YHCS3SvY9n_1OFW9',
  'Academic-Advising-Handbook-CS.pdf': '13EKBPYgPUhFu-d-JowNRsCuW2-kxgp-D',
  'BSC-CS-Courses-Specifications.pdf': '1H6Dxgt8vMToVkiS70XB0xXGDa2Z8B3eO',
  'COE-Student-Handbook.pdf': '1e8XhIEoV0jqV2Z3QcS5sXmpmAHbAM2Ck',
  'CS-GP-Guide_COC_QU_v2-1 (1).pdf': '1EsUscm2UrbKvvKvN1KsOfssUeVzFBREO',
  'CS-GP-Guide_COC_QU_v2-1.pdf': '16Rs19MGKYeNtzBUyDb4mOtpspTCc71Fy',
  'CSC-Master-Academic-Advising-Handbook (1).pdf': '1jPj_9bneKKWkSLi9DOppzfY5XI-d5ZyT',
  'CSC-Master-Academic-Advising-Handbook.pdf': '1Qy9ZUJXoCCszsUD7NebhVPdPUTa2vFBV',
  'CS_ST_Guide_COC_QU.pdf': '1_Q4Yd5k1h-PHwo5oJVLSQKTtUJj0XF_q',
  'IT_Academic_Program_Handbook_for_Faculty.pdf': '1WPiQRmwUPyL6znKgb_hks_CmuxJTeThc',
  'IT_Quality_Manual_Managment_System.pdf': '1WbL-P8cMhNJylIRrdpTPnUxHc1Gv7eaY',
  'Masters-Student-Handbook.pdf': '1Th88ZAlE4eEeNO_s0Q6LtfnnsqdHmy2r',
  'Program-Update-and-Review-Procedures-Guide.pdf': '1O0kzfYbkyODHWM36OMXjTbVKJZkTouS3',
  'Quality_Manual_Managment_System-1.pdf': '1Bi_sI4Xgoh9PA5B3eZDYkc6v_okUzXf7'
};

// ===== Source Viewer — uses Google Drive =====
function openSourceViewer(srcName, pageNum, highlightText) {
  const driveId = DRIVE_MAP[srcName];

  if (!driveId) {
    toast('⚠️ الملف غير متاح حالياً');
    return;
  }

  const previewUrl = `https://drive.google.com/file/d/${driveId}/preview`;
  const viewUrl    = `https://drive.google.com/file/d/${driveId}/view`;

  const existing = document.getElementById('srcViewer');
  if (existing) existing.remove();

  const displayName   = srcName.replace('.pdf','').replace(/-/g,' ').replace(/_/g,' ');
  const decodedHighlight = highlightText.replace(/\\'/g, "'");

  const overlay = document.createElement('div');
  overlay.className = 'viewer-overlay';
  overlay.id = 'srcViewer';
  overlay.innerHTML = `
    <div class="viewer-modal">
      <div class="viewer-header">
        <span>📄 ${esc(displayName)} — ص ${pageNum}</span>
        <button class="viewer-close" onclick="document.getElementById('srcViewer').remove()">✕</button>
      </div>
      <div class="viewer-body">
        <p style="color:var(--muted);font-size:12px;margin-bottom:8px;">النص المُستشهد به:</p>
        <blockquote style="border-right:3px solid var(--gold);padding:8px 12px;margin:0 0 12px 0;background:rgba(200,151,58,0.06);border-radius:4px;font-size:13px;color:var(--text)">${esc(decodedHighlight)}</blockquote>
        <div style="text-align:center;margin-bottom:10px;">
          <a href="${viewUrl}" target="_blank" style="color:var(--green);font-weight:600;font-size:13px;">🔗 افتح الملف كاملاً في Drive →</a>
        </div>
        <iframe
          src="${previewUrl}"
          style="width:100%;height:420px;border:1px solid var(--border);border-radius:8px;"
          allow="autoplay">
        </iframe>
      </div>
    </div>`;

  document.body.appendChild(overlay);
  overlay.addEventListener('click', e => { if (e.target === overlay) overlay.remove(); });
}

function addOOS(text){
  const ca=document.getElementById('ca');
  const w=document.createElement('div'); w.className='mr bot';
  w.innerHTML='<div class="oos-card">'+
    '<div class="oos-icon">🔍</div>'+
    '<div class="oos-text">'+esc(text).replace(/\n/g,'<br>')+'</div>'+
    '<div class="oos-hint">💡 جرّب إعادة الصياغة أو اختر من الأسئلة الشائعة أدناه</div>'+
    '<div class="oos-chips">'+
      '<button class="bc oos-chip" onclick="pick(this)">متطلبات التخرج</button>'+
      '<button class="bc oos-chip" onclick="pick(this)">سياسة الغياب</button>'+
      '<button class="bc oos-chip" onclick="pick(this)">شروط التدريب الميداني</button>'+
    '</div>'+
  '</div>';
  ca.appendChild(w); ca.scrollTop=ca.scrollHeight;
}

async function feedback(msgId,helpful){
  const row=document.getElementById('fb_'+msgId);
  if(!row) return;
  if(helpful){stats.helpful++;}else{stats.notHelpful++;}
  updateStats();
  try{
    await fetch(API+'/feedback',{
      method:'POST',
      headers:{'Content-Type':'application/json','ngrok-skip-browser-warning':'true'},
      body:JSON.stringify({question:'',answer:'',rating:helpful?5:1})
    });
  }catch(e){}
  row.innerHTML='<span class="fb-done">'+(helpful?'👍 شكراً! سعيد أنها أفادتك':'👎 شكراً على ملاحظتك — سنحسّن')+'</span>';
}

function newChat(){ history=[]; studentInfo={};
  document.getElementById('ca').innerHTML='';
  document.getElementById('ca').style.display='none';
  document.getElementById('wlc').style.display='flex';
  document.querySelector('.bchips').style.display='flex';
}
function startChat(){
  document.getElementById('wlc').style.display='none';
  document.querySelector('.bchips').style.display='none';
  const ca=document.getElementById('ca');
  ca.style.display='flex';ca.style.flexDirection='column';
  ca.innerHTML='';
  const w=document.createElement('div');w.className='mr bot';
  w.innerHTML='<div class="bot-card" style="background:rgba(250,247,242,0.97);border-radius:14px;padding:14px 18px;box-shadow:0 4px 20px rgba(0,0,0,0.18);max-width:460px;font-size:14px;line-height:1.75;color:#1a2e1f;">مرحباً! أنا <strong>لوجوس</strong>، مساعدك الأكاديمي الشخصي في كلية الحاسب 👋<br>كيف أقدر أساعدك اليوم؟</div>';
  ca.appendChild(w);
}
function setNav(el){
  document.querySelectorAll('.ni').forEach(n=>n.classList.remove('active'));
  el.classList.add('active');
  if(!el.textContent.includes('المساعد')) toast('هذه الميزة قيد التطوير 🚧');
}
function pick(el){if(document.getElementById('wlc').style.display!='none'){startChat();}document.getElementById('q').value=el.textContent.trim();send();}
function kd(e){if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send();}}
function rsz(el){el.style.height='auto';el.style.height=Math.min(el.scrollHeight,108)+'px';}
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function toast(msg){const t=document.getElementById('toast');t.textContent=msg;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),3000);}