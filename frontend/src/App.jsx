import { useAudit } from "./hooks/useAudit"
import AuditForm from "./components/AuditForm"

export default function App() {
  const { loading, error, result, runAudit, reset } = useAudit()

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-6 py-12">
        <div className="mb-10">
          <h1 className="text-2xl font-semibold text-gray-900">LLM Judge Consistency Auditor</h1>
          <p className="text-gray-500 mt-1 text-sm">
            Detect positional bias, inter-judge disagreement, and evaluation instability.
          </p>
        </div>

        {!result && (
          <div className="bg-white border border-gray-200 rounded-xl p-8">
            <AuditForm onSubmit={runAudit} loading={loading} />
          </div>
        )}

        {error && (
          <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-700">
            {error}
          </div>
        )}

        {result && (
          <div>
            <button onClick={reset} className="mb-6 text-sm text-gray-500 hover:text-gray-800">
              ← Run another audit
            </button>
            <pre className="bg-white border border-gray-200 rounded-xl p-6 text-xs overflow-auto">
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        )}

        {loading && (
          <div className="mt-6 text-center text-sm text-gray-500">
            Calling judges concurrently — this takes 5-15 seconds...
          </div>
        )}
      </div>
    </div>
  )
}