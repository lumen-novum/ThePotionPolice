import React, { useMemo } from 'react'
import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
  TimeScale
} from 'chart.js'
import 'chartjs-adapter-date-fns'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend, TimeScale)

export default function LevelChart({ cauldron, currentTime }) {
  const data = useMemo(() => {
    const labels = (cauldron?.levels || []).map(p => new Date(p.t))
    const values = (cauldron?.levels || []).map(p => p.level)
    return {
      labels,
      datasets: [
        {
          label: 'Level',
          data: values,
          borderColor: 'rgba(99,102,241,1)',
          backgroundColor: 'rgba(99,102,241,0.2)',
          tension: 0.2,
          pointRadius: 0
        }
      ]
    }
  }, [cauldron])

  const options = useMemo(() => ({
    responsive: true,
    scales: {
      x: { type: 'time', time: { unit: 'minute' } },
      y: { beginAtZero: true, suggestedMax: 100 }
    },
    plugins: {
      legend: { display: false }
    }
  }), [])

  return (
    <div className="bg-white/5 p-4 rounded shadow">
      <h3 className="text-lg font-bold mb-2">{cauldron?.name || 'Cauldron'}</h3>
      <div style={{ height: 240 }}>
        <Line data={data} options={options} />
      </div>
    </div>
  )
}
