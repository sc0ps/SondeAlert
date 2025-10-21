// @ts-nocheck
// SondeAlert – frontend script (Leaflet kaart + live sondes)

let map;
let meMarker;
let sondeLayer = L.layerGroup();
let pollMs = 5000;

function fmtKm(m) {
  return (m / 1000).toFixed(2) + " km";
}
function fmtAlt(a) {
  return a == null || isNaN(a) ? "—" : Math.round(a) + " m";
}

// Icons
const iconMe = L.icon({
  iconUrl: "https://cdn-icons-png.flaticon.com/512/1946/1946429.png", // persoon
  iconSize: [32, 32],
  iconAnchor: [16, 32],
});

const iconSonde = L.icon({
  iconUrl: "https://cdn-icons-png.flaticon.com/512/616/616408.png", // satelliet
  iconSize: [28, 28],
  iconAnchor: [14, 28],
});

function ensureMap() {
  if (map) return;
  map = L.map("map", { zoomControl: true }).setView([52.09, 5.12], 8);

  // OpenStreetMap layer
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  }).addTo(map);

  sondeLayer.addTo(map);
}

function drawMe(lat, lon) {
  if (!map) return;
  if (!meMarker) {
    meMarker = L.marker([lat, lon], { icon: iconMe });
    meMarker.addTo(map);
  }
  meMarker.setLatLng([lat, lon]);
}

function drawSondes(items) {
  sondeLayer.clearLayers();
  if (!items || !items.length) return;
  for (const s of items) {
    const marker = L.marker([s.lat, s.lon], { icon: iconSonde });
    const html = `
      <strong>${s.id || "Sonde"}</strong><br/>
      Afstand: ${fmtKm(s.dist_m)}<br/>
      Hoogte: ${fmtAlt(s.alt)}<br/>
      Laatst: ${s.last || "—"}<br/>
      Plaats: ${s.place || "—"}
    `;
    marker.bindPopup(html);
    marker.addTo(sondeLayer);
  }
}

function renderList(items) {
  const list = document.getElementById("list");
  if (!list) return;
  list.innerHTML = "";
  if (!items || !items.length) {
    list.innerHTML =
      '<div class="meta">Geen sondes binnen de ingestelde afstand.</div>';
    return;
  }
  for (const s of items) {
    const el = document.createElement("div");
    el.className = "item";
    el.innerHTML = `
      <div class="title">${s.id || "Sonde"} <span class="meta">(${
      s.status || "—"
    })</span></div>
      <div class="meta">Afstand: ${fmtKm(s.dist_m)} · Hoogte: ${fmtAlt(
      s.alt
    )} · Plaats: ${s.place || "—"}</div>
    `;
    list.appendChild(el);
  }
}

function setGpsStatus(have, lat, lon) {
  const el = document.getElementById("gpsStatus");
  if (!el) return;
  el.textContent = have
    ? `GPS: ${lat.toFixed(5)}, ${lon.toFixed(5)}`
    : "GPS: geen fix";
}

async function fetchNearest() {
  try {
    const res = await fetch("/nearest.json", { cache: "no-store" });
    const json = await res.json();
    ensureMap();

    const have = !!json.gps?.have;
    const lat = json.gps?.lat || 52.09;
    const lon = json.gps?.lon || 5.12;

    setGpsStatus(have, lat, lon);
    drawMe(lat, lon);
    drawSondes(json.items || []);
    renderList(json.items || []);

    if (!fetchNearest.didFit) {
      map.setView([lat, lon], 9);
      fetchNearest.didFit = true;
    }

    document.getElementById("lastUpdate").textContent =
      new Date().toLocaleTimeString();
  } catch (e) {
    console.warn("fetchNearest error:", e);
  }
}

function startPolling() {
  fetchNearest();
  setInterval(fetchNearest, pollMs);

  const btn = document.getElementById("forceRefresh");
  if (btn) btn.addEventListener("click", fetchNearest);
}

window.addEventListener("DOMContentLoaded", startPolling);
