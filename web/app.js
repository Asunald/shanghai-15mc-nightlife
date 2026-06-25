const state = {
  mode: "walk",
  layer: "composite",
  geojson: null,
  metadata: null,
  mapLayer: null,
  selectedId: null,
  recommendedIds: new Set(),
};

const modePrefix = {
  walk: "w",
  bike: "b",
  transit: "t",
  car: "c",
};

const layerSuffix = {
  composite: "c",
  baseline: "b",
  track: "t",
};

const map = L.map("map", {
  zoomControl: true,
  preferCanvas: true,
}).setView([31.23, 121.47], 10);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 18,
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
}).addTo(map);

function scoreKey() {
  if (state.layer === "composite" && state.mode === "walk") return "w_c";
  return `${modePrefix[state.mode]}_${layerSuffix[state.layer]}`;
}

function scoreFor(feature, key = scoreKey()) {
  return Number(feature.properties[key] ?? feature.properties.cs ?? 0);
}

function featureFromHex(row) {
  const ring = h3.cellToBoundary(row.h, true);
  ring.push(ring[0]);
  return {
    type: "Feature",
    id: row.h,
    properties: row,
    geometry: {
      type: "Polygon",
      coordinates: [ring],
    },
  };
}

function colorFor(score) {
  if (score >= 85) return "#b3261e";
  if (score >= 70) return "#d65f2f";
  if (score >= 55) return "#ee9b39";
  if (score >= 35) return "#f4c95d";
  if (score >= 15) return "#b9d38a";
  if (score > 0) return "#e5edc6";
  return "#f7f8ed";
}

function styleFeature(feature) {
  const id = feature.properties.h || feature.id;
  const score = scoreFor(feature);
  const recommended = state.recommendedIds.has(id);
  const selected = state.selectedId === id;
  return {
    color: selected ? "#111827" : recommended ? "#083344" : "#ffffff",
    weight: selected ? 2.2 : recommended ? 1.6 : 0.35,
    opacity: selected || recommended ? 0.95 : 0.55,
    fillColor: colorFor(score),
    fillOpacity: score > 0 ? 0.74 : 0.18,
  };
}

function splitList(text) {
  return String(text || "")
    .split(";")
    .map((item) => item.trim())
    .filter(Boolean)
    .slice(0, 5);
}

function updateDetails(feature) {
  const p = feature.properties;
  state.selectedId = p.h || feature.id;
  renderDetails(feature);
  state.mapLayer.setStyle(styleFeature);
}

function renderDetails(feature) {
  const p = feature.properties;
  const amenities = splitList(p.am);
  const detail = document.getElementById("details");
  const layerLabel = state.layer === "track" ? "nightlife" : state.layer;
  detail.innerHTML = `
    <p class="eyebrow">Selected Hex</p>
    <h2>${p.d || "Unknown district"}</h2>
    <div class="pill-row">
      <span class="pill">H3 ${p.h}</span>
      <span class="pill">${String(p.a || "").replace("-", " ")}</span>
      <span class="pill">Rent band: ${p.r || "n/a"} proxy</span>
      <span class="pill">Metro: ${formatDistance(p.md)}</span>
    </div>
    <div class="score-grid">
      <div class="score-tile"><span>Baseline</span><strong>${Number(p.bs).toFixed(0)}</strong></div>
      <div class="score-tile"><span>Nightlife</span><strong>${Number(p.ts).toFixed(0)}</strong></div>
      <div class="score-tile"><span>Composite</span><strong>${Number(p.cs).toFixed(0)}</strong></div>
    </div>
    <p class="muted">Mode view: ${state.mode}. Current ${layerLabel} score: ${scoreFor(feature).toFixed(1)}.</p>
    <h3>Top amenities</h3>
    <ol class="amenities">
      ${amenities.map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>No named amenities in this hex.</li>"}
    </ol>
    <h3>Nightlife counts</h3>
    <p class="muted">Restaurants ${p.pr || 0}, bars/nightlife ${p.pb || 0}, culture venues ${p.pc || 0}, convenience ${p.pv || 0}, metro proxy ${p.pm || 0}.</p>
  `;
}

function formatDistance(value) {
  const meters = Number(value);
  if (!Number.isFinite(meters)) return "n/a";
  if (meters >= 1000) return `${(meters / 1000).toFixed(1)} km`;
  return `${Math.round(meters)} m`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function attachFeature(feature, layer) {
  layer.on({
    click: () => updateDetails(feature),
    mouseover: () => layer.setStyle({ weight: 1.3, opacity: 0.85 }),
    mouseout: () => {
      if (state.mapLayer) state.mapLayer.resetStyle(layer);
    },
  });
  layer.bindTooltip(`${feature.properties.d || "Shanghai"} - ${scoreFor(feature).toFixed(0)}`, {
    sticky: true,
    direction: "top",
    opacity: 0.9,
  });
}

function renderLayer() {
  if (state.mapLayer) {
    map.removeLayer(state.mapLayer);
  }
  state.mapLayer = L.geoJSON(state.geojson, {
    style: styleFeature,
    onEachFeature: attachFeature,
  }).addTo(map);
}

function refreshLayer() {
  if (!state.mapLayer) return;
  state.mapLayer.setStyle(styleFeature);
  const feature = selectedFeature();
  if (feature) renderDetails(feature);
}

function selectedFeature() {
  if (!state.selectedId || !state.geojson) return null;
  return state.geojson.features.find((feature) => (feature.properties.h || feature.id) === state.selectedId) || null;
}

function setActiveButton(groupId, attr, value) {
  document.querySelectorAll(`#${groupId} button`).forEach((button) => {
    button.classList.toggle("active", button.dataset[attr] === value);
  });
}

function wireControls() {
  document.querySelectorAll("#modeControls button").forEach((button) => {
    button.addEventListener("click", () => {
      state.mode = button.dataset.mode;
      setActiveButton("modeControls", "mode", state.mode);
      refreshLayer();
    });
  });
  document.querySelectorAll("#layerControls button").forEach((button) => {
    button.addEventListener("click", () => {
      state.layer = button.dataset.layer;
      setActiveButton("layerControls", "layer", state.layer);
      refreshLayer();
    });
  });

  const baseline = document.getElementById("baselineWeight");
  const track = document.getElementById("trackWeight");
  const baselineOut = document.getElementById("baselineWeightOut");
  const trackOut = document.getElementById("trackWeightOut");
  const syncOut = () => {
    baselineOut.value = baseline.value;
    trackOut.value = track.value;
  };
  baseline.addEventListener("input", syncOut);
  track.addEventListener("input", syncOut);
  document.getElementById("findTop").addEventListener("click", highlightRecommendations);
}

function highlightRecommendations() {
  const baselineWeight = Number(document.getElementById("baselineWeight").value);
  const trackWeight = Number(document.getElementById("trackWeight").value);
  const total = Math.max(1, baselineWeight + trackWeight);
  const ranked = [...state.geojson.features]
    .map((feature) => ({
      id: feature.properties.h,
      score: (Number(feature.properties.bs) * baselineWeight + Number(feature.properties.ts) * trackWeight) / total,
    }))
    .sort((a, b) => b.score - a.score)
    .slice(0, 10);
  state.recommendedIds = new Set(ranked.map((item) => item.id));
  document.getElementById("recommendCount").textContent = "Top 10 highlighted";
  refreshLayer();
  const topFeature = state.geojson.features.find((feature) => feature.properties.h === ranked[0]?.id);
  if (topFeature) {
    updateDetails(topFeature);
    map.flyTo([topFeature.properties.y, topFeature.properties.x], 13, { duration: 0.7 });
  }
}

function renderTransparency() {
  const el = document.getElementById("transparencyContent");
  const sources = state.metadata.data_sources
    .map((source) => `<li><strong>${escapeHtml(source.name)}</strong>: ${escapeHtml(source.used_for)} Limitation: ${escapeHtml(source.limitations)}</li>`)
    .join("");
  const limits = state.metadata.limitations.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
  el.innerHTML = `
    <ul>
      <li>Displayed hexes: ${(state.metadata.web_hex_count || state.metadata.hex_count).toLocaleString()} of ${state.metadata.hex_count.toLocaleString()} modeled H3 cells at resolution ${state.metadata.h3_resolution}.</li>
      <li>Composite: ${escapeHtml(state.metadata.scoring.composite)}.</li>
    </ul>
    <h3>Sources</h3>
    <ul>${sources}</ul>
    <h3>Limitations</h3>
    <ul>${limits}</ul>
  `;
}

async function init() {
  wireControls();
  const [hexPayload, metadata] = await Promise.all([
    fetch("./data/hexes.json").then((response) => response.json()),
    fetch("./data/metadata.json").then((response) => response.json()),
  ]);
  state.geojson = {
    type: "FeatureCollection",
    features: hexPayload.hexes.map(featureFromHex),
  };
  state.metadata = metadata;
  renderLayer();
  renderTransparency();
  const bounds = state.mapLayer.getBounds();
  if (bounds.isValid()) map.fitBounds(bounds.pad(0.04));
  document.getElementById("loading").classList.add("hidden");
}

init().catch((error) => {
  console.error(error);
  const loading = document.getElementById("loading");
  loading.textContent = "Could not load map data. Start a local server from the web folder.";
});
