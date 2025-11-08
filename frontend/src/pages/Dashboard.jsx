import React, { useState } from 'react'
import Map from '../components/Map'
import LevelChart from '../components/LevelChart'
import TicketTable from '../components/TicketTable'

export default function Dashboard() {
  const [currentTime, setCurrentTime] = useState(null)
  const [selected, setSelected] = useState(null)

  // slider value will be timestamp in ms; for scaffold we derive a range from now - 24h to now
  const now = Date.now()
  const start = now - 1000 * 60 * 60 * 24

  function handleSlider(e) {
    const v = Number(e.target.value)
    setCurrentTime(v || null)
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2">
          <Map currentTime={currentTime} onSelectCauldron={(c) => setSelected(c)} />
          <div className="mt-3 bg-white/5 p-3 rounded">
            <input
              type="range"
              min={start}
              max={now}
              onChange={handleSlider}
              defaultValue={now}
              className="w-full"
            />
            <div className="text-xs text-white/70 mt-2">Current time: {currentTime ? new Date(currentTime).toLocaleString() : 'Live'}</div>
          </div>
        </div>

        <div className="col-span-1 space-y-4">
          <div>
            <h2 className="text-xl font-bold mb-2">Selected Cauldron</h2>
            {selected ? <LevelChart cauldron={selected} currentTime={currentTime} /> : <div className="p-4 bg-white/5 rounded">Click a cauldron to view details</div>}
          </div>

          <TicketTable />
        </div>
      </div>
    </div>
  )
}
