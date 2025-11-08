import React, { useEffect, useState, useCallback } from 'react'
import { MapContainer, TileLayer, Polyline } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import CauldronMarker from './CauldronMarker'

export default function Map({ currentTime, onSelectCauldron }) {
  const [cauldrons, setCauldrons] = useState([])
  const [paths, setPaths] = useState([])

  useEffect(() => {
    let mounted = true
    async function load() {
      try {
        const [cRes, pRes] = await Promise.all([
          fetch('/api/cauldrons'),
          fetch('/api/network-map')
        ])
        const [cjson, pjson] = await Promise.all([cRes.json(), pRes.json()])
        if (!mounted) return
        setCauldrons(Array.isArray(cjson) ? cjson : [])
        setPaths(Array.isArray(pjson) ? pjson : [])
      } catch (err) {
        console.error('Map load error', err)
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
