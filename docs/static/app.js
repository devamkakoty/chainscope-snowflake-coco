"use strict";
const $ = (s) => document.querySelector(s);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const icon = (name) => `<svg class="icon" aria-hidden="true"><use href="./static/icons.svg#${name}"></use></svg>`;
const names = {overview:"Overview",copilot:"Ask copilot",ontology:"Supply network",catalog:"Metric catalog",audit:"Audit trail"};
const typeNames = {suppliers:"Supplier",parts:"Part",plants:"Plant",shipments:"Shipment",orders:"Order",customers:"Customer"};
const typeIcons = {suppliers:"users",parts:"package",plants:"factory",shipments:"truck",orders:"book-open",customers:"users"};
const state = {view:"overview", overview:null, answer:null, selected:"", query:0, page:0, record:0, trace:"ORD-013", graph:null, busy:false};

async function api(path, body) {
  if (window.CHAINSCOPE_REPLAY) return window.CHAINSCOPE_REPLAY.api(path, body);
  const response = await fetch(path, body === undefined ? {} : {
    method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)
  });
  const data = await response.json();
  if (!response.ok) throw Object.assign(new Error(data.message || "Request failed."), {data,status:response.status});
  return data;
}
function toast(text) {
  $("#toast").textContent = text; $("#toast").hidden = false;
  clearTimeout(toast.timer); toast.timer = setTimeout(() => {$("#toast").hidden = true;}, 2800);
}
function heading(kicker,title,subtitle,action="") {
  return `<div class="page-heading"><div><span class="eyebrow">${esc(kicker)}</span><h1>${esc(title)}</h1><p class="subheading">${esc(subtitle)}</p></div>${action || `<div class="date-badge">${icon("clock")}04 Oct 2026</div>`}</div>`;
}
function chip(s) {
  return `<button class="source-chip" data-table="${esc(s.table)}" data-record="${esc(s.id)}" title="Open ${esc(s.table)} source ${esc(s.id)}">${esc(s.id)}</button>`;
}
function evidence(sources, compact=false) {
  const chips = `<div class="source-chips">${sources.map(chip).join("")}</div>`;
  return compact ? `<details><summary>${sources.length} records</summary>${chips}</details>` : chips;
}
function sourceButton(table,id,label) {
  return `<button class="text-action" data-table="${esc(table)}" data-record="${esc(id)}">${esc(label || id)}</button>`;
}
function networkStrip(counts) {
  return `<div class="network-strip">${Object.entries(typeNames).map(([key,label]) => `<div class="network-type"><span>${icon(typeIcons[key])}</span><strong>${label}</strong><small>${counts[key]} records</small></div>`).join("")}</div>
    <div class="network-note">${icon("shield-check")}Explicit sourcing, inventory and order-allocation relationships<span>&middot;</span>Record-level provenance</div>`;
}
function rateBar(value) {
  const bounded = Math.max(0,Math.min(100,value ?? 0));
  // SVG widths are numeric attributes, not inline styles, so the strict CSP is retained.
  return `<span class="rate"><svg width="66" height="5" viewBox="0 0 100 5" aria-hidden="true"><rect width="100" height="5" rx="2" fill="#e8ecea"/><rect width="${bounded}" height="5" rx="2" fill="${bounded < 50 ? "#d18a68" : "#559a80"}"/></svg>${value === null ? "N/A" : esc(value)+"%"}</span>`;
}
function overviewView(data) {
  const labels = [["Awaiting receipt","status-red"],["Action needed","status-amber"],["Unit-weighted","status-green"],["Concentrated","status-purple"]];
  return heading("OPERATIONS / CONTROL ROOM","Supply chain overview","One connected network. Every number accounted for.") +
    `<div class="kpi-grid">${data.kpis.map((k,i) => `<button class="kpi" data-ask="${k.id}"><div class="kpi-heading">${esc(k.title)}${icon("arrow-up-right")}</div><div class="kpi-value">${esc(k.metric.display)}<span class="kpi-status ${labels[i][1]}">${labels[i][0]}</span></div><div class="kpi-note"><span>${k.sources} linked source records</span><span>As of Oct 04</span></div></button>`).join("")}</div>
    <section class="section"><div class="section-heading"><div><h2>Your supply network</h2><p>From approved suppliers to customer commitments</p></div><a class="text-action" href="#ontology">Explore network ${icon("arrow-up-right")}</a></div>${networkStrip(data.counts)}</section>
    <div class="overview-bottom"><section class="section"><div class="section-heading"><div><h2>Supplier reliability</h2><p>On-time delivery &middot; ${esc(data.on_time)} network-wide</p></div><button class="text-action" data-ask="supplier_reliability">View evidence ${icon("arrow-up-right")}</button></div>
      <div class="table-wrap"><table><thead><tr><th>SUPPLIER</th><th>DUE</th><th>ON-TIME RATE</th></tr></thead><tbody>${data.suppliers.map(s => `<tr><td><span class="supplier-name">${sourceButton("suppliers",s.id,s.supplier)}</span><span class="supplier-region">${esc(s.region)}</span></td><td>${s.due_shipments}</td><td>${rateBar(s.on_time_pct)}</td></tr>`).join("")}</tbody></table></div></section>
      <section class="section"><div class="section-heading"><div><h2>Inventory watchlist</h2><p>Positions below approved safety stock</p></div><button class="text-action" data-ask="plant_shortages">View all ${icon("arrow-up-right")}</button></div>
      ${data.shortages.slice(0,4).map(r=>`<div class="risk-item"><span class="risk-icon">${icon("package")}</span><div><h3>${sourceButton("inventory",r.id,r.part)}</h3><p>${esc(r.plant)} &middot; ${r.on_hand} / ${r.safety_stock} units</p></div><span class="gap">-${r.shortage_units} units</span></div>`).join("")}
      <div class="copilot-banner"><div><h3>From signal to source.</h3><p>7 governed business questions</p></div><a href="#copilot" class="primary-button">Ask copilot ${icon("arrow-right")}</a></div></section></div>`;
}
function copilotView(data) {
  return heading("GOVERNED ANALYTICS","Ask the supply chain","Approved questions. Reproducible answers. Inspectable evidence.") +
    `<div class="copilot-layout"><aside class="question-sidebar"><h2>Approved questions</h2><div class="question-list">${data.catalog.map(m=>`<button class="question-option ${state.selected===m.id?"selected":""}" data-ask="${m.id}">${icon(m.available?"messages-square":"lock-keyhole")}<span>${esc(m.question)}</span></button>`).join("")}</div><div class="question-meta">Metric contract v1.0 &middot; Frozen snapshot<br>Exact questions and approved aliases</div></aside>
    <section aria-label="Copilot conversation"><form class="ask-form" id="ask-form"><label class="sr-only" for="question-input">Business question</label><input id="question-input" maxlength="500" required autocomplete="off" placeholder="Which customer orders are at risk?" value="${esc(state.answer?.question || "")}"><button type="submit" title="Ask question" aria-label="Ask question">${icon("send")}</button></form><div id="answer-area" aria-live="polite">${state.answer?answerView(state.answer):`<div class="empty-state">${icon("messages-square")}<h2>Supply chain copilot</h2><p>7 approved questions &middot; ${esc(data.role_label)}<br>Snapshot: 04 October 2026</p></div>`}</div></section></div>`;
}
function answerView(a) {
  if(a.status==="refused") return `<div class="refusal"><div class="badge status-amber">${icon("shield-check")}Policy decision</div><h2>${a.error==="forbidden_metric"?"Commercial access required":"Outside the approved catalog"}</h2><p>${esc(a.message)}</p></div>`;
  return `<div class="answer-meta"><span class="badge status-green">${icon("shield-check")}Governed answer</span><span>${esc(a.policy.role_label)}</span><span>&middot;</span><span>Decision #${a.audit_sequence ?? "local"}</span></div>
    <div class="answer-heading"><div><h2>${esc(a.title)}</h2><div class="answer-value">${esc(a.metric.display)}${a.metric.unit!=="%"&&a.metric.unit!=="USD"?`<small>${esc(a.metric.unit)}</small>`:""}</div></div><button id="export-answer" class="icon-button" title="Download answer and citations" aria-label="Download answer and citations">${icon("download")}</button></div>
    <p class="answer-summary">${esc(a.summary)}</p>
    <div class="table-wrap"><table class="answer-table"><thead><tr>${a.columns.map(c=>`<th>${esc(c[1])}</th>`).join("")}<th>SOURCE RECORDS</th></tr></thead><tbody>${a.rows.map(r=>`<tr>${a.columns.map(c=>`<td>${esc(r[c[0]] ?? "N/A")}</td>`).join("")}<td>${evidence(r.sources,true)}</td></tr>`).join("") || `<tr><td colspan="${a.columns.length+1}">No matching records in this snapshot.</td></tr>`}</tbody></table></div>
    <details class="calculation"><summary>Metric definition &amp; approved SQL</summary><p>${esc(a.definition)}</p><p><strong>Grain:</strong> ${esc(a.grain)}</p><pre>${esc(a.sql)}</pre></details>
    <div class="evidence-strip">${icon("check")} ${a.citations.length} distinct source records ${chip({table:"snapshot",id:"SC-20261004"})}<span>Snapshot 04 Oct 2026</span></div>`;
}
function catalogView(data) {
  return heading("SEMANTIC CONTRACT","Metric catalog","Explicit grain, access policy and business definitions.")+
    `<div class="catalog-grid">${data.catalog.map((m,i)=>`<article class="metric-card"><header><div><span class="eyebrow">METRIC ${String(i+1).padStart(2,"0")}</span><h2>${esc(m.title)}</h2></div><span class="badge ${m.available?"status-green":"status-amber"}">${m.roles.length===2?"Operations":"Commercial"}</span></header><p>${esc(m.definition)}</p><div class="grain"><strong>Grain:</strong> ${esc(m.grain)}</div><div class="section-heading"><code>${esc(m.id)}</code><button class="text-action" data-ask="${m.id}">Run question ${icon("arrow-up-right")}</button></div></article>`).join("")}</div>`;
}
function auditView(data) {
  let chain=true;
  for(let i=1;i<data.entries.length;i++) if(data.entries[i].previous_sha256!==data.entries[i-1].sha256) chain=false;
  return heading("GOVERNANCE","Decision audit trail","Allowed, denied and unsupported questions in this browser session.")+
    `<div class="audit-info">${icon("shield-check")} ${chain?"Hash links continuous":"Hash link mismatch"} &middot; ${data.entries.length} retained decisions &middot; In-memory, not externally attested</div>`+
    (data.entries.length?`<div class="table-wrap"><table><thead><tr><th>DECISION</th><th>TIME (LOCAL)</th><th>METRIC</th><th>ROLE</th><th>RESULT</th><th>SHA-256</th></tr></thead><tbody>${[...data.entries].reverse().map(e=>`<tr><td>#${e.sequence}</td><td>${esc(new Date(e.at).toLocaleTimeString("en-GB"))}</td><td>${esc(e.metric_id)}</td><td>${esc(e.role)}</td><td><span class="badge ${e.decision==="allowed"?"status-green":"status-amber"}">${esc(e.decision)}</span></td><td class="hash" title="${esc(e.sha256)}">${esc(e.sha256.slice(0,14))}...</td></tr>`).join("")}</tbody></table></div>`:`<div class="empty-state">${icon("shield-check")}<h2>No decisions yet</h2><p>Current session &middot; 0 approved queries executed</p></div>`);
}
async function ontologyView(graph) {
  const traced = await api(`/api/records/orders/${state.trace}`);
  const traceSources = [];
  for(const ref of traced.related.filter(s=>s.table==="order_lines")){
    const line=await api(ref.href);
    traceSources.push(line.source,...line.related);
    for(const alloc of line.related.filter(s=>s.table==="allocations")){
      const a=await api(alloc.href);
      traceSources.push(a.source,...a.related);
      const shipRef=a.related.find(s=>s.table==="shipments");
      if(shipRef){const s=await api(shipRef.href);traceSources.push(s.source,...s.related);}
    }
  }
  const refs=[traced.source,...traced.related,...traceSources];
  const ids=new Set(refs.map(s=>s.id));
  const points = new Map();
  const widths = {suppliers:132,parts:124,plants:120,shipments:105,orders:110,customers:125};
  graph.path.forEach((type,col)=>{
    const group=graph.nodes.filter(n=>n.table===type);
    group.forEach((n,i)=>points.set(n.id,{x:18+col*168,y:55+(i+0.5)*(620/group.length),w:widths[type]}));
  });
  const edges=graph.edges.map(e=>{
    const a=points.get(e.from),b=points.get(e.to), traced=ids.has(e.from)&&ids.has(e.to)&&ids.has(e.via);
    return `<path class="graph-edge ${traced?"traced":""}" d="M ${a.x+a.w} ${a.y} C ${a.x+a.w+28} ${a.y}, ${b.x-28} ${b.y}, ${b.x} ${b.y}"/>`;
  }).join("");
  const nodes=graph.nodes.map(n=>{
    const p=points.get(n.id), short=n.table==="shipments"||n.table==="orders"?n.id:n.name;
    return `<g class="graph-node ${ids.has(n.id)?"traced":""}" role="button" tabindex="0" aria-label="Source ${esc(n.id)}, ${esc(n.name)}" data-table="${n.table}" data-record="${n.id}"><title>${esc(n.id)}: ${esc(n.name)}</title><rect x="${p.x}" y="${p.y-8}" width="${p.w}" height="16"/><text x="${p.x+6}" y="${p.y+3}">${esc(short)}</text></g>`;
  }).join("");
  const unique=[...new Map(refs.map(s=>[s.id,s])).values()];
  return heading("CONNECTED ONTOLOGY","Supply network","Supplier to customer, with explicit shipment-to-order allocations.")+
    `<div class="graph-toolbar"><span class="badge status-green">${graph.nodes.length} entities &middot; ${graph.edges.length} relationships</span><label>Trace order<select id="trace-select">${graph.nodes.filter(n=>n.table==="orders").map(n=>`<option ${n.id===state.trace?"selected":""}>${n.id}</option>`).join("")}</select></label></div>
    <div class="graph-scroll"><svg class="ontology-graph" viewBox="0 0 1010 715" role="group" aria-label="Source-linked supply chain network">${graph.path.map((t,i)=>`<text class="graph-column" x="${18+i*168}" y="27">${typeNames[t].toUpperCase()}</text>`).join("")}${edges}${nodes}</svg></div>
    <div class="graph-legend"><span><span class="legend-line"></span>${state.trace} evidence path</span><span><span class="legend-line muted-line"></span>Other source relationships</span><span>Inbound shipments &middot; No bill-of-material conversion</span></div>
    <div class="trace-evidence"><h3>${state.trace} / Source records</h3>${evidence(unique)}</div>`;
}
async function navigate() {
  const view=location.hash.slice(1) || "overview", page=++state.page;
  state.view=names[view]?view:"overview";
  state.query++;
  state.busy=false;
  document.querySelectorAll("[data-view]").forEach(a=>{a.classList.toggle("active",a.dataset.view===state.view); if(a.dataset.view===state.view)a.setAttribute("aria-current","page");else a.removeAttribute("aria-current");});
  $("#breadcrumb-current").textContent=names[state.view];
  $("#main").innerHTML='<div class="loading-state">Loading snapshot...</div>';
  try {
    let content;
    if(state.view==="audit") content=auditView(await api("/api/audit"));
    else if(state.view==="ontology"){state.graph=await api("/api/ontology");content=await ontologyView(state.graph);}
    else {
      state.overview=await api("/api/overview");
      $("#role-select").value=state.overview.role;
      content=state.view==="copilot"?copilotView(state.overview):state.view==="catalog"?catalogView(state.overview):overviewView(state.overview);
    }
    if(page===state.page)$("#main").innerHTML=content;
  } catch(error) {
    if(page===state.page)$("#main").innerHTML=`<div class="error-banner">${esc(error.message)} <button class="text-action" id="retry">Retry</button></div>`;
  }
}
async function ask(question) {
  if(state.view!=="copilot") {
    history.pushState(null,"","#copilot");
    await navigate();
  }
  const sequence=++state.query;
  state.busy=true;
  const area=$("#answer-area");
  if(!area)return;
  area.innerHTML='<div class="loading-inline">Evaluating metric and source records...</div>';
  $("#ask-form button").disabled=true;
  const m=state.overview.catalog.find(m=>m.id===question);
  state.selected=m?.id || "";
  $("#question-input").value=m?.question || question;
  document.querySelectorAll(".question-option").forEach(b=>b.classList.toggle("selected",b.dataset.ask===state.selected));
  try {
    const response=await api("/api/ask",{question});
    if(sequence!==state.query)return;
    state.answer=response;
  } catch(error) {
    if(sequence!==state.query)return;
    state.answer=error.data || {status:"refused",message:error.message,error:"network_error"};
  }
  if(sequence===state.query&&$("#answer-area")){
    $("#answer-area").innerHTML=answerView(state.answer);
    $("#ask-form button").disabled=false;
    state.busy=false;
  }
}
async function openRecord(table,id) {
  const sequence=++state.record;
  const dialog=$("#source-dialog");
  $("#source-content").innerHTML='<div class="loading-inline">Loading source record...</div>';
  if(!dialog.open)dialog.showModal();
  try {
    const data=await api(`/api/records/${encodeURIComponent(table)}/${encodeURIComponent(id)}`);
    if(sequence!==state.record)return;
    $("#source-content").innerHTML=`<span class="badge status-green">Synthetic source</span><h2 id="source-title">${esc(id)}</h2><p class="source-class">${esc(table)} &middot; Snapshot 04 Oct 2026</p><dl class="record-fields">${Object.entries(data.record).map(([k,v])=>`<dt>${esc(k)}</dt><dd>${v===null?"Not received":esc(v)}</dd>`).join("")}</dl>${data.redacted_fields.length?`<div class="redaction-note">${icon("lock-keyhole")} Restricted fields: ${esc(data.redacted_fields.join(", "))}</div>`:""}<h3 class="related-title">Related source records</h3>${evidence(data.related)}`;
  } catch(error){if(sequence===state.record)$("#source-content").innerHTML=`<h2 id="source-title">Record unavailable</h2><p>${esc(error.message)}</p>`;}
}
document.addEventListener("click",(event)=>{
  const askButton=event.target.closest("[data-ask]");
  const recordButton=event.target.closest("[data-record]");
  if(askButton)ask(askButton.dataset.ask);
  else if(recordButton)openRecord(recordButton.dataset.table,recordButton.dataset.record);
  else if(event.target.closest("#close-source")){$("#source-dialog").close();state.record++;}
  else if(event.target.closest("#retry"))navigate();
  else if(event.target.closest("#export-answer")&&state.answer){
    const blob=new Blob([JSON.stringify(state.answer,null,2)],{type:"application/json"});
    const url=URL.createObjectURL(blob),a=document.createElement("a");
    a.href=url;a.download=`chainscope-${state.answer.metric_id}-20261004.json`;a.click();
    setTimeout(()=>URL.revokeObjectURL(url),1000);toast("Answer and citations exported.");
  }
});
document.addEventListener("keydown",e=>{
  if((e.key==="Enter"||e.key===" ")&&e.target.matches(".graph-node")){e.preventDefault();openRecord(e.target.dataset.table,e.target.dataset.record);}
});
document.addEventListener("submit",e=>{if(e.target.id==="ask-form"){e.preventDefault();ask($("#question-input").value);}});
document.addEventListener("change",async e=>{
  if(e.target.id==="role-select"){
    e.target.disabled=true;
    state.query++;state.record++;state.answer=null;state.selected="";
    $("#source-dialog").close();
    try{await api("/api/session",{role:e.target.value});await navigate();toast("Demo identity changed. Previous answer cleared.");}
    catch(error){toast(error.message);}
    finally{e.target.disabled=false;}
  } else if(e.target.id==="trace-select"){
    state.trace=e.target.value;await navigate();
  }
});
window.addEventListener("hashchange",navigate);
navigate();
