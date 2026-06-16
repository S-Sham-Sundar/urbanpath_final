/**
 * app.js — Map Explorer
 * Developer B: Ajith
 * Plain JavaScript — no frameworks
 */

const API = 'http://localhost:8000'
let map, routeLayer, markerLayer
let selectedAlgo = 'astar'
let searchDebounce = null

// ── INIT MAP ──────────────────────────────────────────────────────────────────

function initMap() {
  map = L.map('map').setView([13.0827, 80.2707], 12)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap'
  }).addTo(map)
}

// ── ALGORITHM TOGGLE ──────────────────────────────────────────────────────────

function setAlgo(algo) {
  selectedAlgo = algo
  document.getElementById('btnAstar').classList.toggle('active', algo === 'astar')
  document.getElementById('btnDijkstra').classList.toggle('active', algo === 'dijkstra')
}

// ── SEARCH (TRIE AUTOCOMPLETE) ────────────────────────────────────────────────

document.getElementById('searchInput').addEventListener('input', function () {
  const q = this.value.trim()
  clearTimeout(searchDebounce)
  if (!q) { closeDropdown(); return }

  searchDebounce = setTimeout(async () => {
    try {
      const res = await fetch(`${API}/api/search?q=${encodeURIComponent(q)}&limit=8`)
      if (!res.ok) return
      const results = await res.json()
      renderDropdown(results)
    } catch {
      closeDropdown()
    }
  }, 200)
})

function renderDropdown(results) {
  const dd = document.getElementById('searchDropdown')
  dd.innerHTML = ''
  if (results.length === 0) { closeDropdown(); return }

  results.forEach(r => {
    const li = document.createElement('li')
    li.innerHTML = `<span>${r.name}</span><span class="type-tag">${r.type}</span>`
    li.addEventListener('mousedown', () => {
      document.getElementById('searchInput').value = r.name
      closeDropdown()
      // Drop a marker on the map
      if (markerLayer) map.removeLayer(markerLayer)
      markerLayer = L.marker([r.lat, r.lon])
        .addTo(map)
        .bindPopup(r.name)
        .openPopup()
      map.setView([r.lat, r.lon], 14)
    })
    dd.appendChild(li)
  })
  dd.classList.add('open')
}

function closeDropdown() {
  document.getElementById('searchDropdown').classList.remove('open')
}

document.addEventListener('click', (e) => {
  if (!e.target.closest('.search-wrap')) closeDropdown()
})

// ── ROUTE FINDER ──────────────────────────────────────────────────────────────

async function findRoute() {
  const src = document.getElementById('srcNode').value
  const dst = document.getElementById('dstNode').value
  const errorBox = document.getElementById('errorBox')
  const resultCard = document.getElementById('resultCard')

  if (!src || !dst) { showError('Enter both source and destination node IDs'); return }

  errorBox.classList.add('hidden')
  resultCard.classList.add('hidden')
  if (routeLayer) map.removeLayer(routeLayer)

  try {
    const res = await fetch(`${API}/api/route?src=${src}&dst=${dst}&algorithm=${selectedAlgo}`)
    if (!res.ok) throw new Error('No path found between these nodes')
    const data = await res.json()

    // Draw polyline
    const coords = data.path_coords.map(p => [p.lat, p.lon])
    routeLayer = L.polyline(coords, { color: '#E8662C', weight: 5, opacity: 0.9 }).addTo(map)
    map.fitBounds(routeLayer.getBounds(), { padding: [40, 40] })

    // Start / end markers
    L.marker(coords[0]).addTo(map).bindPopup('Start')
    L.marker(coords[coords.length - 1]).addTo(map).bindPopup('End')

    // Show result
    document.getElementById('resultDist').innerHTML =
      `${data.distance.toFixed(2)} <span class="result-unit">km</span>`
    document.getElementById('resultAlgo').textContent =
      selectedAlgo === 'astar' ? 'A* — Haversine heuristic' : "Dijkstra's — custom MinHeap"
    resultCard.classList.remove('hidden')

  } catch (e) {
    showError(e.message)
  }
}

function showError(msg) {
  const box = document.getElementById('errorBox')
  box.textContent = msg
  box.classList.remove('hidden')
}

// ── START ─────────────────────────────────────────────────────────────────────
initMap()
