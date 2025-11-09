import React from 'react'
import { Marker, Popup } from 'react-leaflet'
import L from 'leaflet'
import potionGreen from '../assets/cauldrons/potion-green.svg'

function createDivIcon(cauldron, currentLevelPercent) {
  const html = `
    <div style="display:flex;flex-direction:column;align-items:center;font-size:12px;">
      <div style="width:36px;height:36px;border-radius:50%;background:rgba(255,255,255,0.9);display:flex;align-items:center;justify-content:center;color:#111;font-weight:700;">
        ${Math.round(currentLevelPercent)}%
      </div>
      <div style="margin-top:4px;background:rgba(0,0,0,0.6);color:#fff;padding:2px 6px;border-radius:4px;font-size:11px;">${cauldron.name || 'Cauldron'}</div>
    </div>`
  return new L.DivIcon({ html, className: '' })
}

export default function CauldronMarker({ cauldron, currentTime, onClick }) {
  // cauldron object is expected to contain `levels` array of { t: timestamp, level: number }
  let percent = 0
  if (Array.isArray(cauldron.levels) && cauldron.levels.length) {
    if (currentTime == null) {
      // show latest
      const last = cauldron.levels[cauldron.levels.length - 1]
      percent = (last.level || 0)
    } else {
      // find nearest time
      const idx = cauldron.levels.findIndex(l => l.t >= currentTime)
      const item = idx === -1 ? cauldron.levels[cauldron.levels.length - 1] : cauldron.levels[idx]
      percent = item ? item.level : 0
    }
  }

  // Use a uniform potion-green SVG icon for all cauldrons on the map
  const icon = new L.Icon({
    iconUrl: potionGreen,
    iconSize: [40, 40],
    iconAnchor: [20, 40],
    popupAnchor: [0, -40]
  })

  return (
    <Marker
      position={[cauldron.lat || 0, cauldron.lng || 0]}
      icon={icon}
      eventHandlers={{ click: onClick }}
    >
      <Popup>
        <div>
          <strong>{cauldron.name}</strong>
          <div>Level: {Math.round(percent)}%</div>
          <div>ID: {cauldron.id}</div>
        </div>
      </Popup>
    </Marker>
  )
}
