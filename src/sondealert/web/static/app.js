// SondeAlert frontend logica
<strong>${s.id || 'Sonde'}</strong><br/>
Afstand: ${fmtKm(s.dist_m)}<br/>
Hoogte: ${fmtAlt(s.alt)}<br/>
Laatst: ${s.last || '—'}<br/>
Plaats: ${s.place || '—'}
`);
marker.addTo(layer);
});
}


function fitBounds(items, have, lat, lon){
const bounds = [];
if (have) bounds.push([lat, lon]);
(items||[]).forEach(s => bounds.push([s.lat, s.lon]));
if (bounds.length){
map.fitBounds(bounds, { padding: [40,40] });
}
}


function renderList(items){
const list = document.getElementById('list');
if (!list) return;
list.innerHTML = '';
if (!items || !items.length){
list.innerHTML = '<div class="meta">Geen sondes binnen de ingestelde afstand.</div>';
return;
}
for (const s of items){
const el = document.createElement('div');
el.className = 'item';
el.innerHTML = `
<div class="title">${s.id || 'Sonde'} <span class="meta">(${s.status || '—'})</span></div>
<div class="meta">Afstand: ${fmtKm(s.dist_m)} · Hoogte: ${fmtAlt(s.alt)} · Plaats: ${s.place || '—'}</div>
`;
list.appendChild(el);
}
}


async function fetchNearest(){
try {
const res = await fetch('/nearest.json', { cache: 'no-store' });
const json = await res.json();
lastJson = json;
document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();


ensureMap();
const have = !!json.gps?.have;
const lat = json.gps?.lat || 0;
const lon = json.gps?.lon || 0;


setGpsStatus(have, lat, lon);
if (have){ drawMe(lat, lon); }


drawSondes(json.items || []);
renderList(json.items || []);


// Alleen auto-zoomen bij eerste load of wanneer er nog geen bounds staan
if (!fetchNearest.didFit){
fitBounds(json.items || [], have, lat, lon);
fetchNearest.didFit = true;
}
} catch (e){
console.warn('fetchNearest error', e);
}
}


function startPolling(){
fetchNearest();
setInterval(fetchNearest, pollMs);
const btn = document.getElementById('forceRefresh');
if (btn) btn.addEventListener('click', fetchNearest);
}


window.addEventListener('DOMContentLoaded', startPolling);