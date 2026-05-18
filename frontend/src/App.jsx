import React, { useState } from 'react'
import Editor from '@monaco-editor/react'

export default function App() {
  const [code, setCode] = useState('2 + 3 * 4')
  const [out, setOut] = useState('')
  const [err, setErr] = useState('')
  const [running, setRunning] = useState(false)

  async function run() {
    setRunning(true)
    setOut('Ejecutando...')
    setErr('')
    try {
      const res = await fetch('http://127.0.0.1:8000/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, mode: 'interpret' })
      })
      const j = await res.json()
      setOut(j.stdout ?? '')
      setErr(j.stderr ?? (j.success ? '' : JSON.stringify(j)))
    } catch (e) {
      setErr(String(e))
      setOut('')
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="h-screen flex flex-col">
      <header className="p-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white flex items-center justify-between">
        <h1 className="text-lg font-semibold">Mini Intesrprete</h1>
        <div className="flex gap-2">
          <button
            onClick={run}
            disabled={running}
            className="px-4 py-2 bg-white text-blue-600 rounded shadow"
          >
            {running ? 'Ejecutando…' : 'Run'}
          </button>
        </div>
      </header>

      <main className="flex-1 flex">
        <section className="w-2/3 p-4">
          <Editor
            height="70vh"
            defaultLanguage="javascript"
            value={code}
            onChange={(v) => setCode(v)}
            options={{ minimap: { enabled: false } }}
          />
        </section>

        <aside className="w-1/3 p-4 border-l">
          <div className="mb-4">
            <h2 className="font-medium">Output</h2>
            <pre className="mt-2 p-2 bg-gray-900 text-white rounded h-40 overflow-auto">{out}</pre>
          </div>
          {err && (
            <div className="rounded-lg border border-rose-200 bg-rose-50 p-3">
              <div className="flex items-center justify-between gap-3">
                <h2 className="font-medium text-rose-700">Ayuda</h2>
                <span className="rounded-full bg-amber-100 px-2 py-1 text-xs font-medium text-amber-800">
                  Sugerencias
                </span>
              </div>
              <p className="mt-2 text-sm text-rose-700">Te ayudo con esto</p>
              <pre className="mt-2 h-36 overflow-auto rounded bg-rose-100 p-2 text-rose-900">{err}</pre>
            </div>
          )}
        </aside>
      </main>
    </div>
  )
}
