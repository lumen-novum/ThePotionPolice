import React, { useEffect, useState } from 'react'

export default function TicketTable() {
  const [tickets, setTickets] = useState([])

  useEffect(() => {
    let mounted = true
    async function load() {
      try {
        const res = await fetch('/api/tickets')
        const json = await res.json()
        if (!mounted) return
        setTickets(Array.isArray(json) ? json : [])
      } catch (err) {
        console.error('Error loading tickets', err)
      }
    }
    load()
    return () => { mounted = false }
  }, [])

  return (
    <div className="overflow-auto bg-white/5 rounded p-4">
      <h3 className="font-bold mb-2">Tickets</h3>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left">
            <th className="pb-2">ID</th>
            <th className="pb-2">Summary</th>
            <th className="pb-2">Status</th>
            <th className="pb-2">Created</th>
          </tr>
        </thead>
        <tbody>
          {tickets.map(t => (
            <tr key={t.id} className="border-t border-white/5">
              <td className="py-2">{t.id}</td>
              <td className="py-2">{t.summary || t.title}</td>
              <td className="py-2">{t.status}</td>
              <td className="py-2">{t.created_at || t.created}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
