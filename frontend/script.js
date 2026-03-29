// script.js  –  ResQFlow client-side logic
// Every function calls a real Flask API endpoint.

const API = window.location.origin;

// ── State ──────────────────────────────────────────────────────────────────────
let CU = null;           // current user  {username, role}
let DISASTERS = [];
let VOLUNTEERS = [];
let MAIN_MAP  = null;
let EDGE_LAYERS = [], DISASTER_LAYERS = [], VOL_LAYERS = [];

// ── Utility ────────────────────────────────────────────────────────────────────
function $(id){ return document.getElementById(id); }
function show(id){ $(id).classList.remove('hidden'); }
function hide(id){ $(id).classList.add('hidden'); }
function setMsg(id, txt, ok=true){ const e=$(id); if(!e) return; e.textContent=txt; e.className=ok?'msg-ok':'msg-err'; }

function fileToBase64(file){
  return new Promise((res,rej)=>{
    const r=new FileReader();
    r.onload=()=>res(r.result);
    r.onerror=()=>rej(new Error('Read failed'));
    r.readAsDataURL(file);
  });
}

const isAdmin = u => u === 'admin';
const isVol   = u => u && u.startsWith('v');
const isUser  = u => u && u.startsWith('user');

// ── Auth ───────────────────────────────────────────────────────────────────────
async function doLogin(){
  const username = $('u-user').value.trim();
  const password = $('u-pass').value.trim();
  if(!username||!password){ setMsg('login-err','Enter username and password.',false); return; }

  const res  = await fetch(API+'/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username,password})});
  const data = await res.json();

  if(data.success){
    CU = {username:data.username, role:data.role};
    hide('login-box');
    show('app');
    show('hdr-user');
    $('hdr-name').textContent = `${data.username} (${data.role})`;
    setupNav(data.role);
    go('view');
  } else {
    setMsg('login-err', data.message||'Invalid credentials.', false);
  }
}

function setupNav(role){
  if(role==='user')      { show('n-report'); }
  if(role==='volunteer') { show('n-vol');    }
  if(role==='admin')     { show('n-admin'); show('n-algo'); }
}

function logout(){
  CU=null; DISASTERS=[]; VOLUNTEERS=[];
  location.reload();
}

// ── Navigation ─────────────────────────────────────────────────────────────────
const PANELS = ['view','report','volunteer','admin','algo','map'];

function go(name){
  PANELS.forEach(p=>{ hide('p-'+p); const b=$('n-'+p); if(b) b.classList.remove('active'); });
  show('p-'+name);
  const btn = $('n-'+name); if(btn) btn.classList.add('active');

  if(name==='view')      loadDisasters();
  if(name==='admin')     loadAdmin();
  if(name==='volunteer') loadVolHub();
  if(name==='map')       loadMap();
  if(name==='algo')      populateAlgoSelects();
}

// ── Disasters ──────────────────────────────────────────────────────────────────
async function loadDisasters(){
  let url = API+'/api/disasters';
  if(CU && isUser(CU.username)) url += '?reporter_id='+CU.username;

  const res = await fetch(url);
  DISASTERS = await res.json();

  if(CU){
    if(isUser(CU.username))
      $('d-panel-title').textContent = 'Your Submitted Reports (Priority Sorted)';
    else if(isVol(CU.username))
      $('d-panel-title').textContent = 'All Active Disasters';
    else
      $('d-panel-title').textContent = 'All Disaster Reports (Heap Priority Order)';
  }

  renderDisasters();
}

function renderDisasters(){
  const box = $('d-list');
  if(!DISASTERS.length){
    box.innerHTML = '<p class="empty">No disasters reported yet.</p>';
    return;
  }
  box.innerHTML = DISASTERS.map(d=>{
    const canDel = CU && isUser(CU.username) && d.reported_by===CU.username && d.status==='Pending';
    const statusCls = {Pending:'b-pend',InProgress:'b-prog',Resolved:'b-res'}[d.status]||'b-pend';
    return `
    <div class="d-card ${d.is_emergency?'d-emg':'d-norm'}">
      <div class="d-head">
        <div>
          <div class="d-title">
            #${d.id} — ${d.type} &nbsp;@&nbsp; ${d.location}
            &nbsp;<span class="badge ${d.is_emergency?'b-emg':'b-norm'}">${d.is_emergency?'⚠️ CRITICAL':'Standard'}</span>
            &nbsp;<span class="badge" style="background:#374151;color:#fff">Severity ${d.severity}/10</span>
          </div>
          <div class="d-sub">Reported by <strong>${d.reported_by}</strong> · ${d.timestamp}</div>
        </div>
        <div style="display:flex;gap:6px;align-items:center;flex-shrink:0">
          <span class="badge ${statusCls}">${d.status}</span>
          ${canDel?`<button class="btn-red btn-xs" onclick="doDeleteDisaster(${d.id})">Delete</button>`:''}
        </div>
      </div>
      <div class="d-body">${d.description||'No description.'}</div>
      <div class="d-foot">
        <span>Supplies: <strong>${d.supplies_needed||'None'}</strong></span>
        <span>Personnel: ${d.assignedCount}/${d.volunteers_needed} assigned</span>
      </div>
      ${d.assigned_volunteers&&d.assigned_volunteers.length
        ?`<div class="d-assigned">Assigned: ${d.assigned_volunteers.join(', ')}</div>`:''}
      ${renderFieldUpdates(d.updates)}
    </div>`;
  }).join('');
}

function renderFieldUpdates(updates){
  if(!updates||!updates.length) return '';
  return `<div style="margin-top:10px;border-top:1px solid var(--bord);padding-top:8px">
    <p style="font-size:.76rem;font-weight:600;color:var(--muted);margin-bottom:5px">Field Updates (${updates.length})</p>
    ${updates.map(u=>`
    <div class="upd upd-${u.priority.toLowerCase()}">
      <strong>[${u.priority}]</strong> ${u.description}
      <span style="font-size:.71rem;color:var(--muted);margin-left:8px">— ${u.volunteer_id} at ${u.timestamp}</span>
    </div>`).join('')}
  </div>`;
}

// ── User: Report ───────────────────────────────────────────────────────────────
async function doReport(){
  const type  = $('r-type').value;
  const loc   = $('r-loc').value;
  const sev   = $('r-sev').value;
  const vol   = $('r-vol').value;

  if(!type||!loc||!sev||!vol){
    setMsg('r-msg','Please fill all required fields.',false); return;
  }

  const photoFile = $('r-photo').files[0];
  let photoB64 = null;
  if(photoFile) photoB64 = await fileToBase64(photoFile);

  const res = await fetch(API+'/api/report',{
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({
      type, location:loc,
      severity:parseInt(sev),
      volunteers_needed:parseInt(vol),
      is_emergency: $('r-emg').checked,
      supplies_needed: $('r-sup').value,
      description: $('r-desc').value,
      reported_by: CU.username,
      report_photo: photoB64
    })
  });
  const data = await res.json();
  if(data.success){
    setMsg('r-msg','✅ '+data.message,true);
    ['r-type','r-loc','r-sev','r-vol','r-sup','r-desc'].forEach(id=>$(id).value='');
    $('r-emg').checked=false; $('r-photo').value='';
  } else {
    setMsg('r-msg','❌ '+(data.error||'Failed'),false);
  }
}

async function doDeleteDisaster(id){
  if(!confirm(`Delete Disaster #${id}?`)) return;
  const res = await fetch(API+'/api/delete-disaster',{
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({disaster_id:id, reporter_id:CU.username})
  });
  const data = await res.json();
  alert(data.message||data.error);
  loadDisasters();
}

// ── Admin Panel ────────────────────────────────────────────────────────────────
async function loadAdmin(){
  await loadDisasters();
  const vres = await fetch(API+'/api/volunteers');
  VOLUNTEERS = await vres.json();
  renderVolGrid();
  populateAdminSelects();
}

function renderVolGrid(){
  const g = $('a-vol-grid'); if(!g) return;
  g.innerHTML = VOLUNTEERS.map(v=>`
  <div class="v-card ${v.is_available?'v-avail':'v-busy'}">
    <div class="v-id">${v.id}</div>
    <div class="v-name">${v.name}</div>
    <div class="v-group">${v.group}</div>
    <div class="v-loc">📍 ${v.location||'?'}</div>
    <span class="badge ${v.is_available?'b-res':'b-pend'}" style="margin-top:4px;display:inline-block">
      ${v.is_available?'Available':'Busy → #'+v.assigned_to}
    </span>
  </div>`).join('');
}

function populateAdminSelects(){
  const active = DISASTERS.filter(d=>d.status!=='Resolved');
  const avail  = VOLUNTEERS.filter(v=>v.is_available);
  const dOpts  = `<option value="">-- Select Disaster --</option>`+active.map(d=>`<option value="${d.id}">#${d.id} ${d.type} @ ${d.location}</option>`).join('');
  const vOpts  = `<option value="">-- Select Volunteer --</option>`+avail.map(v=>`<option value="${v.id}">${v.id} ${v.name} (${v.group})</option>`).join('');

  ['a-dsel','a-rsel','a-updsel'].forEach(id=>{ const e=$(id); if(e) e.innerHTML=dOpts; });
  const vs=$('a-vsel'); if(vs) vs.innerHTML=vOpts;
}

async function doAssign(){
  const did = $('a-dsel').value;
  const vid = $('a-vsel').value;
  if(!did||!vid){ setMsg('a-amsg','Select both a disaster and a volunteer.',false); return; }

  const res = await fetch(API+'/api/assign',{
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({
      disaster_id: parseInt(did),
      volunteer_id: vid,
      deployment_message: $('a-dmsg').value||'Deployment initiated.'
    })
  });
  const data = await res.json();
  setMsg('a-amsg', data.message||data.error, !!data.success);
  loadAdmin();
}

async function doAutoAssign(){
  const did = $('a-dsel').value;
  if(!did){ setMsg('a-amsg','Select a disaster first.',false); return; }

  const res = await fetch(API+'/api/auto-assign',{
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({
      disaster_id: parseInt(did),
      deployment_message: $('a-dmsg').value||'Auto-deployment initiated.'
    })
  });
  const data = await res.json();
  setMsg('a-amsg', data.message||data.error, !!data.success);
  loadAdmin();
}

async function doResolve(){
  const did = $('a-rsel').value;
  if(!did){ setMsg('a-resmsg','Select a disaster.',false); return; }
  if(!confirm(`Mark Disaster #${did} as RESOLVED?`)) return;

  let photoB64 = null;
  const pf = $('a-rphoto').files[0];
  if(pf) photoB64 = await fileToBase64(pf);

  const res = await fetch(API+'/api/resolve',{
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({disaster_id:parseInt(did), resolution_photo:photoB64})
  });
  const data = await res.json();
  setMsg('a-resmsg', data.message||data.error, !!data.success);
  $('a-rphoto').value='';
  loadAdmin();
}

function showUpdates(){
  const did = parseInt($('a-updsel').value);
  const box = $('a-updates');
  if(!did){ box.innerHTML=''; return; }
  const d = DISASTERS.find(x=>x.id===did);
  if(!d||!d.updates||!d.updates.length){
    box.innerHTML='<p class="empty">No field updates yet.</p>'; return;
  }
  box.innerHTML = d.updates.map(u=>`
  <div class="upd upd-${u.priority.toLowerCase()}">
    <div style="display:flex;justify-content:space-between;margin-bottom:3px">
      <strong>[${u.priority}]</strong> from <strong>${u.volunteer_id}</strong>
      <span style="font-size:.71rem;color:var(--muted)">${u.timestamp}</span>
    </div>
    <p>${u.description}</p>
  </div>`).join('');
}

// ── Volunteer Hub ──────────────────────────────────────────────────────────────
async function loadVolHub(){
  if(!CU||!isVol(CU.username)) return;

  const res  = await fetch(API+'/api/volunteer-mission?volunteer_id='+CU.username);
  const data = await res.json();

  if(data.error||!data.assigned_to){
    show('v-no-mission'); hide('v-mission'); return;
  }
  hide('v-no-mission'); show('v-mission');

  const d = data.disaster_details;
  if(d){
    $('v-mission-grid').innerHTML = [
      ['Disaster ID', '#'+d.id], ['Type', d.type], ['Location', d.location],
      ['Severity', d.severity+'/10'], ['Status', d.status], ['Priority', d.priority_type]
    ].map(([l,v])=>`<div class="mis-stat"><span class="lbl">${l}</span><span class="val">${v}</span></div>`).join('');
  }
  $('v-admin-msg').textContent = data.admin_message||'No instructions.';
  const tm = data.team_members||[];
  $('v-team').textContent = tm.length ? tm.join(', ') : 'You are the only assigned volunteer.';
}

async function loadVolRoute(){
  const mres = await fetch(API+'/api/volunteer-mission?volunteer_id='+CU.username);
  const md   = await mres.json();
  if(!md.assigned_to){ alert('You are not on a mission.'); return; }

  const res  = await fetch(API+'/api/route',{
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({volunteer_id:CU.username, disaster_id:md.assigned_to})
  });
  const data = await res.json();
  showRouteResult('v-route-result','vol-route-map',data);
}

async function doSendUpdate(){
  const mres = await fetch(API+'/api/volunteer-mission?volunteer_id='+CU.username);
  const md   = await mres.json();
  if(!md.assigned_to){ setMsg('upd-msg','Not on an active mission.',false); return; }

  const desc = $('upd-desc').value.trim();
  if(!desc){ setMsg('upd-msg','Description required.',false); return; }

  let photoB64=null;
  const pf=$('upd-photo').files[0];
  if(pf) photoB64=await fileToBase64(pf);

  const res = await fetch(API+'/api/volunteer-update',{
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({
      disaster_id: md.assigned_to,
      volunteer_id: CU.username,
      priority: $('upd-pri').value,
      description: desc,
      update_photo: photoB64
    })
  });
  const data = await res.json();
  setMsg('upd-msg', data.success?'✅ Update sent to admin.':'❌ '+(data.error||'Failed'), !!data.success);
  if(data.success){ $('upd-desc').value=''; $('upd-photo').value=''; }
}

// ── Map ────────────────────────────────────────────────────────────────────────
async function loadMap(){
  const res  = await fetch(API+'/api/map-data');
  const data = await res.json();

  if(!MAIN_MAP){
    MAIN_MAP = L.map('main-map').setView([data.center.lat, data.center.lon], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'© OpenStreetMap'}).addTo(MAIN_MAP);
  }
  [...EDGE_LAYERS,...DISASTER_LAYERS,...VOL_LAYERS].forEach(l=>MAIN_MAP.removeLayer(l));
  EDGE_LAYERS=[]; DISASTER_LAYERS=[]; VOL_LAYERS=[];

  // Road edges
  data.graph.edges.forEach(e=>{
    const a=data.graph.nodes.find(n=>n.id===e.from);
    const b=data.graph.nodes.find(n=>n.id===e.to);
    if(a&&b){
      const l=L.polyline([[a.lat,a.lon],[b.lat,b.lon]],{color:'#f97316',weight:1.5,opacity:.5,dashArray:'5,5'})
              .bindTooltip(`${e.from} ↔ ${e.to} (${e.weight} km)`).addTo(MAIN_MAP);
      EDGE_LAYERS.push(l);
    }
  });
  // Location labels
  data.graph.nodes.forEach(n=>{
    const l=L.marker([n.lat,n.lon],{icon:L.divIcon({className:'map-lbl',html:`<span>${n.id}</span>`})}).addTo(MAIN_MAP);
    EDGE_LAYERS.push(l);
  });
  // Disaster markers (red)
  data.disasters.forEach(d=>{
    const icon=L.divIcon({className:'',html:`<div class="mk-dot mk-red">${d.severity}</div>`,iconSize:[26,26]});
    const m=L.marker([d.lat,d.lon],{icon})
      .bindPopup(`<b>#${d.id} ${d.type}</b><br/>Severity: ${d.severity}/10<br/>Status: ${d.status}<br/>${d.is_emergency?'⚠️ CRITICAL':''}`).addTo(MAIN_MAP);
    DISASTER_LAYERS.push(m);
  });
  // Volunteer markers (blue/orange)
  data.volunteers.forEach(v=>{
    const cls=v.is_available?'mk-blue':'mk-orange';
    const icon=L.divIcon({className:'',html:`<div class="mk-dot ${cls}">${v.id.slice(1)}</div>`,iconSize:[26,26]});
    const m=L.marker([v.lat,v.lon],{icon})
      .bindPopup(`<b>${v.id} – ${v.name}</b><br/>Group: ${v.group}<br/>${v.is_available?'✅ Available':'🚨 Deployed → #'+v.assigned_to}`).addTo(MAIN_MAP);
    VOL_LAYERS.push(m);
  });
}

// ── Algorithms ─────────────────────────────────────────────────────────────────
async function populateAlgoSelects(){
  if(!DISASTERS.length){
    const r=await fetch(API+'/api/disasters'); DISASTERS=await r.json();
  }
  if(!VOLUNTEERS.length){
    const r=await fetch(API+'/api/volunteers'); VOLUNTEERS=await r.json();
  }
  const active=DISASTERS.filter(d=>d.status!=='Resolved');
  const dOpts='<option value="">-- Select Disaster --</option>'+active.map(d=>`<option value="${d.id}">#${d.id} ${d.type} @ ${d.location}</option>`).join('');
  const vOpts='<option value="">-- Select Volunteer --</option>'+VOLUNTEERS.map(v=>`<option value="${v.id}">${v.id} ${v.name} (${v.group})</option>`).join('');

  ['dijk-dis','ks-dis','reach-dis'].forEach(id=>{ const e=$(id); if(e) e.innerHTML=dOpts; });
  ['dijk-vol','reach-vol'].forEach(id=>{ const e=$(id); if(e) e.innerHTML=vOpts; });
}

// Heap
async function runHeap(){
  if(!DISASTERS.length){ const r=await fetch(API+'/api/disasters'); DISASTERS=await r.json(); }
  const active=DISASTERS.filter(d=>d.status!=='Resolved');
  const box=$('heap-out'); show('heap-out');
  if(!active.length){ box.innerHTML='<p class="empty">No active disasters in the heap.</p>'; return; }
  box.innerHTML=`
  <div class="algo-box">
    <h4 style="margin-bottom:8px;color:#fff">Heap Order — ${active.length} active disaster(s)</h4>
    <table class="at">
      <thead><tr><th>Rank</th><th>ID</th><th>Type</th><th>Location</th><th>Priority</th><th>Severity</th><th>Reported</th></tr></thead>
      <tbody>${active.map((d,i)=>`
      <tr class="${d.is_emergency?'emg':''}">
        <td>${i+1}</td><td>#${d.id}</td><td>${d.type}</td><td>${d.location}</td>
        <td><span class="badge ${d.is_emergency?'b-emg':'b-norm'}">${d.priority_type}</span></td>
        <td>${d.severity}/10</td><td>${d.timestamp}</td>
      </tr>`).join('')}</tbody>
    </table>
    <p style="font-size:.74rem;color:var(--muted);margin-top:8px">Sort key: (−emergency_flag, −severity, timestamp)</p>
  </div>`;
}

// Dijkstra
async function runDijkstra(){
  const vid=$('dijk-vol').value, did=$('dijk-dis').value;
  if(!vid||!did){ alert('Select a volunteer and a disaster.'); return; }
  const res=await fetch(API+'/api/route',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({volunteer_id:vid,disaster_id:parseInt(did)})});
  const data=await res.json();
  showRouteResult('dijk-out','route-map',data);
}

async function findNearestVol(){
  const did=$('dijk-dis').value;
  if(!did){ alert('Select a disaster.'); return; }
  const res=await fetch(API+'/api/nearest-volunteer',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({disaster_id:parseInt(did)})});
  const data=await res.json();
  const box=$('dijk-out'); show('dijk-out');
  if(data.error){ box.innerHTML=`<p class="algo-err">❌ ${data.error}</p>`; return; }
  box.innerHTML=`<div class="algo-box">
    <h4 style="color:#fff;margin-bottom:6px">Nearest Available Volunteer</h4>
    <p>Volunteer: <strong>${data.volunteer_id}</strong></p>
    <p>Distance: <strong>${data.distance_km} km</strong></p>
    <p>Path: ${data.path?data.path.join(' → '):'N/A'}</p>
  </div>`;
  if(data.coordinates&&data.coordinates.length>1) drawRouteMap('route-map',data.coordinates);
}

function showRouteResult(outId, mapId, data){
  const box=$(outId); show(outId);
  if(data.error){ box.innerHTML=`<p class="algo-err">❌ ${data.error}${data.hint?'<br/>Hint: '+data.hint:''}</p>`; return; }
  box.innerHTML=`<div class="algo-box">
    <h4 style="color:#fff;margin-bottom:8px">Dijkstra Result</h4>
    <table class="at">
      <tr><th>From</th><td>${data.volunteer_location||data.path?.[0]}</td></tr>
      <tr><th>To</th><td>${data.disaster_location||data.path?.[data.path.length-1]}</td></tr>
      <tr><th>Distance</th><td><strong>${data.distance_km} km</strong></td></tr>
      <tr><th>Hops</th><td>${data.steps}</td></tr>
      <tr><th>Path</th><td>${data.path?data.path.join(' → '):'N/A'}</td></tr>
    </table>
  </div>`;
  if(data.coordinates&&data.coordinates.length>1) drawRouteMap(mapId, data.coordinates);
}

function drawRouteMap(containerId, coords){
  const el=$(containerId); show(containerId);
  if(el._map){ el._map.remove(); }
  const m=L.map(containerId).setView([coords[0].lat,coords[0].lon],13);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'© OSM'}).addTo(m);
  L.polyline(coords.map(c=>[c.lat,c.lon]),{color:'#22c55e',weight:4}).addTo(m);
  L.circleMarker([coords[0].lat,coords[0].lon],{radius:9,color:'#3b82f6',fillColor:'#3b82f6',fillOpacity:1}).bindPopup('Start: '+coords[0].name).addTo(m);
  const e=coords[coords.length-1];
  L.circleMarker([e.lat,e.lon],{radius:9,color:'#ef4444',fillColor:'#ef4444',fillOpacity:1}).bindPopup('End: '+e.name).addTo(m);
  coords.forEach(c=>L.circleMarker([c.lat,c.lon],{radius:4,color:'#fff',fillColor:'#f97316',fillOpacity:1}).bindTooltip(c.name).addTo(m));
  el._map=m;
}

// Knapsack

async function runKnapsack(){
  const did=$('ks-dis').value;
  if(!did){ alert('Select a disaster.'); return; }
  const res=await fetch(API+'/api/optimize',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({disaster_id:parseInt(did)})});
  const data=await res.json();
  const box=$('ks-out'); show('ks-out');
  if(data.error){ box.innerHTML=`<p class="algo-err">❌ ${data.error}</p>`; return; }
  const kr=data.knapsack_result, sr=data.supplies_optimization;
  box.innerHTML=`<div class="algo-box">
    <h4 style="color:#fff;margin-bottom:8px">Knapsack DP Result — Disaster #${data.disaster_id} (${data.disaster_type})</h4>
    <table class="at">
      <tr><th>Resource Budget</th><td>${kr.budget} units</td></tr>
      <tr><th>Volunteers Considered</th><td>${kr.all_considered?kr.all_considered.length:0}</td></tr>
      <tr><th>DP Table Cells Computed</th><td>${kr.dp_steps}</td></tr>
      <tr><th>Optimal Skill Score</th><td><strong>${kr.total_value}</strong></td></tr>
      <tr><th>Resources Used</th><td>${kr.total_cost} / ${kr.budget}</td></tr>
    </table>
    <h4 style="color:#d1fae5;margin:10px 0 6px">Selected Volunteers (Optimal Subset)</h4>
    <table class="at">
      <thead><tr><th>ID</th><th>Group</th><th>Skill Value</th><th>Cost</th></tr></thead>
      <tbody>${kr.selected.map(v=>`<tr><td>${v.id}</td><td>${v.group}</td><td>${v.value}</td><td>${v.cost}</td></tr>`).join('')}</tbody>
    </table>
    ${sr?`<p style="margin-top:8px;color:var(--green)">Optimal Supplies: <strong>${sr.selected_supplies.join(', ')||'None matched'}</strong> (${sr.total_weight}/${sr.capacity} units)</p>`:''}
  </div>`;
}


// Union-Find
async function blockRoad(){
  const a=$('uf-from').value, b=$('uf-to').value;
  if(!a||!b){ alert('Select both locations.'); return; }
  const res=await fetch(API+'/api/block-road',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({from:a,to:b})});
  const data=await res.json();
  alert(data.message||data.error);
}

async function unblockRoad(){
  const a=$('uf-from').value, b=$('uf-to').value;
  if(!a||!b){ alert('Select both locations.'); return; }
  const res=await fetch(API+'/api/unblock-road',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({from:a,to:b})});
  const data=await res.json();
  alert(data.message||data.error);
}

async function runUF(){
  const res=await fetch(API+'/api/connectivity',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({blocked_edges:[]})});
  const data=await res.json();
  const box=$('uf-out'); show('uf-out');
  const cls=data.fully_connected?'algo-box':'algo-box algo-warn';
  box.innerHTML=`<div class="${cls}">
    <h4 style="color:#fff;margin-bottom:8px">Union-Find Connectivity Report</h4>
    <table class="at">
      <tr><th>Total Locations</th><td>${data.total_nodes}</td></tr>
      <tr><th>Connected Components</th><td><strong>${data.total_components}</strong></td></tr>
      <tr><th>Active Road Links</th><td>${data.edges_active}</td></tr>
      <tr><th>Blocked Roads</th><td>${data.edges_blocked}</td></tr>
      <tr><th>Fully Connected</th><td>${data.fully_connected?'✅ Yes – All locations reachable':'❌ No – Isolated zones detected!'}</td></tr>
    </table>
    ${data.total_components>1?`<div style="margin-top:10px">${data.components.map(c=>`<div style="background:rgba(249,115,22,.1);border:1px solid var(--orange);border-radius:4px;padding:6px 10px;margin-top:5px;font-size:.79rem">Component (${c.size} nodes): ${c.members.join(', ')}</div>`).join('')}</div>`:'<p style="color:var(--green);margin-top:8px;font-size:.82rem">All city nodes are in one component.</p>'}
    ${data.blocked_roads&&data.blocked_roads.length?`<p style="color:var(--red);font-size:.76rem;margin-top:6px">Blocked: ${data.blocked_roads.map(r=>r.from+'↔'+r.to).join('; ')}</p>`:''}
  </div>`;
}

async function runReach(){
  const vid=$('reach-vol').value, did=$('reach-dis').value;
  if(!vid||!did){ alert('Select a volunteer and disaster.'); return; }
  const res=await fetch(API+'/api/reachability',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({volunteer_id:vid,disaster_id:parseInt(did)})});
  const data=await res.json();
  const box=$('reach-out'); show('reach-out');
  if(data.error){ box.innerHTML=`<p class="algo-err">❌ ${data.error}</p>`; return; }
  box.innerHTML=`<div class="${data.connected?'algo-box':'algo-box algo-warn'}">
    <p>Volunteer <strong>${data.volunteer_id}</strong> @ <strong>${data.location_a}</strong></p>
    <p>Disaster <strong>#${$('reach-dis').value}</strong> @ <strong>${data.location_b}</strong></p>
    <p style="margin-top:8px;font-weight:700">${data.connected?'✅ REACHABLE — Same connected component':'❌ NOT REACHABLE — Route disrupted!'}</p>
    <p style="font-size:.76rem;color:var(--muted);margin-top:4px">Network components: ${data.connectivity_report.total_components}</p>
  </div>`;
}
