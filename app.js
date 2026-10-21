(() => {
  'use strict';
  const { topics, entries } = window.ZHIHENG_GUIDE;
  const $ = selector => document.querySelector(selector);
  const escape = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const savedKey = 'zhiheng-guide-saved-v1';
  const knownIds = new Set(entries.map(item=>item.id));
  const anchor = item => `${item.topic}-${parseInt(item.id.match(/\d+$/)[0],10)}`;
  let saved = new Set(), mode='all', query='', topic='all', brief=false, timer, observer;
  try {const value=JSON.parse(localStorage.getItem(savedKey)||'[]');if(Array.isArray(value))saved=new Set(value.filter(id=>knownIds.has(id)));} catch(_){}
  const searchIndex = new Map(entries.map(item=>[item.id,[item.title,item.lead,item.body,...item.steps,...(item.badges||[]),item.template,item.deliverable,item.review,item.room,item.tags].join(' ').toLocaleLowerCase()]));
  const totalText=`${topics.length} 个主题 · ${entries.length} 条`;
  $('.brand span').textContent=totalText;document.title=`知衡中产指南 · ${totalText}`;
  document.querySelector('meta[name="description"]').content=`知衡中产指南：${totalText}，围绕职业、现金、家庭、教育与生活退路的具体做法。`;
  $('#topic-select').innerHTML += topics.map(t=>`<option value="${t.id}">${t.name}</option>`).join('');
  function notify(message){clearTimeout(timer);$('#toast').textContent=message;$('#toast').classList.add('visible');timer=setTimeout(()=>$('#toast').classList.remove('visible'),2800);}
  function headerSize(){document.documentElement.style.setProperty('--bar-height',`${$('.bar').getBoundingClientRect().height}px`);}
  function syncTheme(){const dark=document.documentElement.dataset.theme==='dark';$('#theme-toggle').setAttribute('aria-label',dark?'切换到日间阅读':'切换到夜间阅读');document.querySelector('meta[name="theme-color"]').content=dark?'#181c23':'#ffffff';}
  function saveState(){try{localStorage.setItem(savedKey,JSON.stringify([...saved]));return true;}catch(_){return false;}}
  function updateControls(){
    for(const [id,value] of [['show-all','all'],['quick-filter','quick'],['saved-filter','saved']]){const active=mode===value;$('#'+id).classList.toggle('active',active);$('#'+id).setAttribute('aria-pressed',String(active));}
    $('#brief-toggle').classList.toggle('active',brief);$('#brief-toggle').setAttribute('aria-pressed',String(brief));document.body.classList.toggle('brief',brief);$('#topic-select').value=topic;
  }
  function entryHTML(item,index){return `<article class="guide-entry" id="${anchor(item)}" data-entry="${item.id}">
    <div class="entry-heading"><span class="item-number">${index+1}</span><h3>${escape(item.title)}</h3><button class="save-entry" data-save="${item.id}" aria-pressed="${saved.has(item.id)}" aria-label="${saved.has(item.id)?'取消收藏':'收藏'}：${escape(item.title)}">${saved.has(item.id)?'已收藏':'收藏'}</button></div>
    <ul class="entry-badges" aria-label="条目标签">${(item.badges||[]).map((badge,i)=>`<li class="badge ${i===0?'badge-kind':''}">${escape(badge)}</li>`).join('')}</ul>
    <p class="plain">${escape(item.lead)}</p>${item.body?`<p class="body-copy">${escape(item.body)}</p>`:''}
    <div class="fields"><div class="field"><b>具体做法</b><ol class="steps">${item.steps.map(step=>`<li>${escape(step)}</li>`).join('')}</ol></div><div class="field"><b>可用模板</b><div class="template">${escape(item.template)}</div></div><div class="field"><b>做完得到</b><div>${escape(item.deliverable)}</div></div><div class="field"><b>怎么判断</b><div>${escape(item.review)}</div></div>${item.room?`<div class="field field-note"><b>适用边界</b><div>${escape(item.room)}</div></div>`:''}</div>
    <div class="entry-actions"><button class="text-button" data-copy="${item.id}">复制执行清单</button><button class="text-button" data-link="${item.id}">复制链接</button></div>
  </article>`;}
  function watchReading(){
    observer?.disconnect();const visible=new Map();
    observer=new IntersectionObserver(changes=>{changes.forEach(entry=>{if(entry.isIntersecting)visible.set(entry.target.id,entry.target);else visible.delete(entry.target.id);});const first=[...visible.values()].sort((a,b)=>a.getBoundingClientRect().top-b.getBoundingClientRect().top)[0];if(!first)return;document.querySelectorAll('.toc-link').forEach(link=>{const active=link.getAttribute('href')==='#'+first.id;link.classList.toggle('current',active);active?link.setAttribute('aria-current','location'):link.removeAttribute('aria-current');});},{rootMargin:`-${Math.ceil($('.bar').getBoundingClientRect().height)}px 0px -45% 0px`,threshold:0});
    document.querySelectorAll('.guide-entry').forEach(item=>observer.observe(item));
  }
  function render(){
    const tokens=query.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
    const matches=entries.filter(item=>(topic==='all'||topic===item.topic)&&(mode!=='quick'||item.quick)&&(mode!=='saved'||saved.has(item.id))&&tokens.every(token=>searchIndex.get(item.id).includes(token)));
    const ids=new Set(matches.map(item=>item.id));let nav='',main='';
    topics.forEach((t,ti)=>{const all=entries.filter(item=>item.topic===t.id),items=all.filter(item=>ids.has(item.id));if(!items.length)return;
      nav+=`<div class="toc-group"><div class="toc-heading"><a href="#section-${t.id}">${ti+1}. ${t.name}</a><span>${items.length} 条</span></div><ol class="toc-list">${items.map(item=>`<li><a class="toc-link" href="#${anchor(item)}"><span class="toc-dot ${item.quick?'quick':''}" aria-hidden="true"></span><span class="toc-num">${all.indexOf(item)+1}</span><span class="toc-title">${escape(item.title)}</span></a></li>`).join('')}</ol></div>`;
      main+=`<section class="topic-section" id="section-${t.id}" aria-labelledby="heading-${t.id}"><div class="section-heading"><h2 id="heading-${t.id}">${ti+1}. ${t.name}</h2><span>${items.length} 条</span></div><p class="intro">${t.intro}</p>${items.map(item=>entryHTML(item,all.indexOf(item))).join('')}</section>`;
    });
    $('#toc-list').innerHTML=nav||'<p class="toc-empty">没有匹配条目</p>';$('#guide-list').innerHTML=main;$('#result-count').textContent=`${matches.length} / ${entries.length} 条`;$('#empty-state').hidden=matches.length>0;
    const noSaved=mode==='saved'&&saved.size===0;$('#empty-title').textContent=noSaved?'还没有收藏的建议':'没有找到相关建议';$('#empty-text').textContent=noSaved?'点击建议旁的“收藏”，以后可以在这里找回。':'试试更短的词，或者取消筛选。';updateControls();watchReading();
  }
  function reset(){mode='all';query='';topic='all';$('#search-input').value='';render();}
  function setMode(next){mode=mode===next&&next!=='all'?'all':next;render();window.scrollTo({top:0,behavior:'instant'});}
  async function copyText(text,message){try{if(!navigator.clipboard?.writeText)throw new Error('Unavailable');await navigator.clipboard.writeText(text);notify(message);}catch(_){$('#copy-text').value=text;$('#copy-dialog').showModal();$('#copy-text').focus();$('#copy-text').select();}}
  function revealHash(){let value;try{value=decodeURIComponent(location.hash.slice(1));}catch(_){return;}const item=entries.find(e=>anchor(e)===value);const targetTopic=topics.find(t=>'section-'+t.id===value);if(!item&&!targetTopic)return;if(!document.getElementById(value)){reset();}requestAnimationFrame(()=>document.getElementById(value)?.scrollIntoView({block:'start'}));}
  document.addEventListener('click',event=>{const button=event.target.closest('button');if(!button)return;
    if(button.dataset.save){const id=button.dataset.save,wasSaved=saved.has(id);wasSaved?saved.delete(id):saved.add(id);const persisted=saveState();if(mode==='saved'&&wasSaved){render();$('#saved-filter').focus();}else{button.setAttribute('aria-pressed',String(!wasSaved));button.textContent=wasSaved?'收藏':'已收藏';button.setAttribute('aria-label',`${wasSaved?'收藏':'取消收藏'}：${entries.find(e=>e.id===id).title}`);}notify(persisted?(wasSaved?'已取消收藏':'已收藏，只保存在当前浏览器'):'暂时无法持久保存，收藏在本次打开期间可用');return;}
    if(button.dataset.copy){const item=entries.find(e=>e.id===button.dataset.copy);copyText(`${item.title}\n\n${item.lead}\n\n具体做法\n${item.steps.map((step,i)=>`${i+1}. ${step}`).join('\n')}\n\n可用模板\n${item.template}\n\n做完得到\n${item.deliverable}\n\n怎么判断\n${item.review}${item.room?'\n\n适用边界\n'+item.room:''}`,'执行清单已复制，粘贴到笔记即可使用');return;}
    if(button.dataset.link){const item=entries.find(e=>e.id===button.dataset.link);const url=new URL(location.href);url.hash=anchor(item);copyText(url.href,'链接已复制');}
  });
  $('#show-all').addEventListener('click',()=>{reset();window.scrollTo({top:0,behavior:'instant'});});$('#quick-filter').addEventListener('click',()=>setMode('quick'));$('#saved-filter').addEventListener('click',()=>setMode('saved'));
  $('#brief-toggle').addEventListener('click',()=>{brief=!brief;updateControls();});
  $('#search-input').addEventListener('input',event=>{query=event.target.value;render();window.scrollTo({top:0,behavior:'instant'});});
  $('#topic-select').addEventListener('change',event=>{topic=event.target.value;render();window.scrollTo({top:0,behavior:'instant'});});$('#reset-filters').addEventListener('click',reset);
  $('#home-link').addEventListener('click',event=>{event.preventDefault();reset();history.replaceState(null,'',location.pathname+location.search);window.scrollTo({top:0,behavior:'instant'});});
  $('#theme-toggle').addEventListener('click',()=>{document.documentElement.dataset.theme=document.documentElement.dataset.theme==='dark'?'light':'dark';try{localStorage.setItem('zhiheng-guide-theme',document.documentElement.dataset.theme);}catch(_){}syncTheme();});
  $('#back-top').addEventListener('click',()=>window.scrollTo({top:0,behavior:'smooth'}));window.addEventListener('scroll',()=>{$('#back-top').hidden=window.scrollY<500;},{passive:true});$('#close-copy').addEventListener('click',()=>$('#copy-dialog').close());
  document.addEventListener('keydown',event=>{if(event.key==='/'&&!event.target.closest('input,textarea,select,[contenteditable=true]')&&!$('#copy-dialog').open){event.preventDefault();$('#search-input').focus();}if(event.key==='Escape'&&event.target===$('#search-input'))$('#search-input').blur();});
  window.addEventListener('hashchange',revealHash);new ResizeObserver(headerSize).observe($('.bar'));headerSize();syncTheme();render();revealHash();
})();
