import React, { useEffect, useState } from 'react'
import axios from 'axios'

export default function ConsumableApp() {
  const [items, setItems] = useState([])
  const [q, setQ] = useState('')

  useEffect(() => {
    axios.get('/api/consommables/').then(r => setItems(r.data)).catch(console.error)
  }, [])

  const total = items.reduce((s, it) => s + (Number(it.quantity || 0) * Number(it.price_eur || 0)), 0)
  const filtered = items.filter(it => !q || (it.name || '').toLowerCase().includes(q.toLowerCase()) || (it.reference || '').toLowerCase().includes(q.toLowerCase()))

  return (
    <div className="app">
      <header className="app-header">
        <h2>Inventaire — Consommables</h2>
        <div className="total">Valeur totale: <strong>{total.toFixed(2)} €</strong></div>
      </header>

      <div className="controls">
        <input placeholder="Recherche" value={q} onChange={e => setQ(e.target.value)} />
      </div>

      <ul className="list">
        {filtered.map(it => (
          <li key={it.id} className="item">
            <div className="left">
              <div className="name">{it.name}</div>
              <div className="ref">{it.reference}</div>
            </div>
            <div className="right">{it.quantity} × {(it.price_eur || 0).toFixed(2)} €</div>
          </li>
        ))}
      </ul>
    </div>
  )
}
