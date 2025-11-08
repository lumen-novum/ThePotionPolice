import Dashboard from './pages/Dashboard'

export default function App() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-800 text-white p-8">
      <div className="max-w-7xl mx-auto">
        <header className="mb-6">
          <h1 className="text-3xl font-bold">The Potion Police</h1>
          <p className="text-sm text-white/80">Dashboard</p>
        </header>
        <main>
          <Dashboard />
        </main>
      </div>
    </div>
  )
}
