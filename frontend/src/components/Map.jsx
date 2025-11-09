import React, { useEffect, useState, useCallback } from 'react'
import { MapContainer, TileLayer, Polyline } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import CauldronMarker from './CauldronMarker'

export default function Map({ currentTime, onSelectCauldron }) {
  const [cauldrons, setCauldrons] = useState([])
  const [paths, setPaths] = useState([])
  const [error, setError] = useState(null)

  useEffect(() => {
    let mounted = true
    async function load() {
      try {
        // Allow overriding the API host via VITE_API_URL (e.g. http://localhost:5000)
        // Default to local Flask backend when VITE_API_URL is not set so preview
        // or static builds can still reach the API.
        const API_BASE = ((import.meta.env.VITE_API_URL ?? '') || 'http://127.0.0.1:5000').replace(/\/$/, '')
        const apiFetch = (path) => {
          const url = API_BASE ? `${API_BASE}${path}` : path
          return fetch(url)
        }

        const [cRes, pRes] = await Promise.all([
          apiFetch('/api/cauldrons'),
          apiFetch('/api/network-map')
        ])
        const [cjson, pjson] = await Promise.all([cRes.json(), pRes.json()])
        if (!mounted) return
        setCauldrons(Array.isArray(cjson) ? cjson : [])
        setPaths(Array.isArray(pjson) ? pjson : [])
      } catch (err) {
        console.error('Map load error', err)
        setError(err?.message || String(err))
      }
    }
    load()
    return () => { mounted = false }
  }, [])

  const handleMarkerClick = useCallback((cauldron) => {
    if (onSelectCauldron) onSelectCauldron(cauldron)
  }, [onSelectCauldron])

  // center on first cauldron if available
  const center = cauldrons.length ? [cauldrons[0].lat || 0, cauldrons[0].lng || 0] : [0, 0]

  return (
    <div className="h-[60vh] rounded overflow-hidden shadow">
      {error && (
        <div className="absolute z-50 m-3 p-2 bg-red-50 text-red-800 rounded shadow">
          <div className="font-semibold">Map load error</div>
          <div className="text-sm">{error}</div>
          <div className="text-xs text-gray-600">If you're running a preview build, either start the frontend dev server (npm run dev) or set VITE_API_URL to your backend (e.g. http://127.0.0.1:5000) and reload.</div>
        </div>
      )}
      <MapContainer center={center} zoom={13} style={{ height: '100%', width: '100%' }}>
        <TileLayer
          attribution='&copy; OpenStreetMap contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {paths.map((p, i) => {
          // each path is expected to be { coordinates: [[lat,lng], ...] }
          const coords = p.coordinates || []
          return <Polyline key={i} positions={coords} color={p.color || '#888'} />
        })}

        {cauldrons.map(c => (
          <CauldronMarker
            key={c.id}
            cauldron={c}
            currentTime={currentTime}
            onClick={() => handleMarkerClick(c)}
          />
        ))}
      </MapContainer>
    </div>
  )
}
