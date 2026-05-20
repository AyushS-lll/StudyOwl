import { Link } from 'react-router-dom'

export function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-100 p-4">
      <div className="rounded-2xl bg-white p-8 shadow-lg text-center max-w-md">
        <h1 className="text-3xl font-bold text-slate-900 mb-2">🦉 Page not found</h1>
        <p className="text-slate-600 mb-6">
          The owl checked everywhere — that page isn't here.
        </p>
        <Link
          to="/"
          className="inline-flex items-center rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 transition"
        >
          Back home
        </Link>
      </div>
    </div>
  )
}

export default NotFound
