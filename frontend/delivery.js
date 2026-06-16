/**
 * delivery.js — Delivery Planner
 * Developer B: Ajith
 * Plain JavaScript — no frameworks
 */

const API = 'http://localhost:8000'

let stops = [
  { id: 0, lat: 13.0827, lon: 80.2707, name: 'Central Station (Depot)' },
  { id: 1, lat: 13.0500, lon: 80.2824, name: 'Marina Beach' },
  { id: 2, lat: 13.0368, lon: 80.2676, name: 'Mylapore' },
  { id: 3, lat: 13.0012, lon: 80.2565, name: 'Adyar' },
  { id: 4, lat: 13.0418, lon: 80.2341, name: 'T Nagar' },
]

// ── RENDER STOPS ──────────────────────────────────────────────────────────────

function renderStops() {
  const list = document.getElementById('stopsList')
  list.innerHTML = ''
  stops.forEach((s, i) => {
    const div = document.createElement('div')
    div.className = 'stop-item'
    div.innerHTML = `
      <div>
        <div class="stop-name">
          ${i === 0 ? '<span class="depot-tag">DEPOT</span>' : ''}${s.name}
        </div>
        <div class="stop-coords">${s.lat.toFixed(4)}, ${s.lon.toFixed(4)}</div>
      </div>
      ${i > 0 ? `<button class="remove-btn" onclick="removeStop(${s.id})">✕</button>` : ''}
    `
    list.appendChild(div)
  })
}

function removeStop(id) {
  stops = stops.filter(s => s.id !== id)
  renderStops()
}

// ── OPTIMISE ──────────────────────────────────────────────────────────────────

async function optimise() {
  const errorBox = document.getElementById('deliveryError')
  const emptyState = document.getElementById('emptyState')
  const resultSection = document.getElementById('resultSection')

  errorBox.classList.add('hidden')
  emptyState.classList.add('hidden')
  resultSection.classList.add('hidden')

  try {
    const res = await fetch(`${API}/api/delivery`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ stops })
    })
    if (!res.ok) throw new Error('Optimisation failed')
    const data = await res.json()
    renderResult(data)
  } catch (e) {
    errorBox.textContent = e.message
    errorBox.classList.remove('hidden')
    emptyState.classList.remove('hidden')
  }
}

function renderResult(data) {
  document.getElementById('totalDist').textContent = data.estimated_distance.toFixed(4)
  document.getElementById('strategy').textContent = data.strategy === 'exact' ? 'Exact' : 'Clustered'
  document.getElementById('routeAlgoLabel').textContent =
    data.strategy === 'exact'
      ? 'Held-Karp TSP · O(2ⁿ·n²)'
      : 'K-means++ → Held-Karp · O(k·n·iters)'

  const routeOrder = document.getElementById('routeOrder')
  routeOrder.innerHTML = ''
  data.optimal_route.forEach((idx, i) => {
    const stop = stops[idx]
    if (!stop) return
    const div = document.createElement('div')
    div.className = 'route-item'
    div.innerHTML = `
      <span class="route-num">${String(i + 1).padStart(2, '0')}</span>
      <span class="route-name">${stop.name}</span>
    `
    routeOrder.appendChild(div)
  })

  document.getElementById('resultSection').classList.remove('hidden')
}

// ── START ─────────────────────────────────────────────────────────────────────
renderStops()
