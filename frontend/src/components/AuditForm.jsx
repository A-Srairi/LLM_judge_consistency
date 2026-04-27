import { useState } from "react"
import KeyInput from "./KeyInput"

const DEFAULT_JUDGES = [
  "groq/llama-3.3-70b-versatile",
  "groq/llama-3.1-8b-instant",
  "groq/qwen/qwen3-32b",
]

const DEFAULT_CRITERIA = ["accuracy", "helpfulness", "conciseness"]
const TEMPERATURE_OPTIONS = [0.0, 0.3, 0.5, 0.7, 1.0]

export default function AuditForm({ onSubmit, loading }) {
  const [prompt, setPrompt] = useState("")
  const [responseA, setResponseA] = useState("")
  const [responseB, setResponseB] = useState("")
  const [judges, setJudges] = useState(DEFAULT_JUDGES)
  const [criteria, setCriteria] = useState(DEFAULT_CRITERIA)
  const [nSamples, setNSamples] = useState(2)
  const [apiKey, setApiKey] = useState("")
  const [temperatures, setTemperatures] = useState([0.0])

  function toggleJudge(judge) {
    setJudges(prev =>
      prev.includes(judge) ? prev.filter(j => j !== judge) : [...prev, judge]
    )
  }

  function toggleCriterion(c) {
    setCriteria(prev =>
      prev.includes(c) ? prev.filter(x => x !== c) : [...prev, c]
    )
  }

  function toggleTemp(t) {
    setTemperatures(prev =>
      prev.includes(t) ? prev.filter(x => x !== t) : [...prev, t].sort()
    )
  }

  function handleSubmit(e) {
    e.preventDefault()
    if (!prompt || !responseA || !responseB || judges.length === 0) return
    onSubmit({
      prompt,
      response_a: responseA,
      response_b: responseB,
      judges,
      criteria,
      n_samples: nSamples,
      temperatures,
    }, apiKey)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <KeyInput onKeyChange={setApiKey} />

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Prompt</label>
        <textarea
          value={prompt}
          onChange={e => setPrompt(e.target.value)}
          rows={3}
          placeholder="What question or task were both responses trying to answer?"
          className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-gray-400 resize-none"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Response A</label>
          <textarea
            value={responseA}
            onChange={e => setResponseA(e.target.value)}
            rows={6}
            placeholder="First response..."
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-gray-400 resize-none"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Response B</label>
          <textarea
            value={responseB}
            onChange={e => setResponseB(e.target.value)}
            rows={6}
            placeholder="Second response..."
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-gray-400 resize-none"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Judge models</label>
          <div className="space-y-2">
            {DEFAULT_JUDGES.map(judge => (
              <label key={judge} className="flex items-center gap-2 text-sm cursor-pointer">
                <input
                  type="checkbox"
                  checked={judges.includes(judge)}
                  onChange={() => toggleJudge(judge)}
                  className="rounded"
                />
                <span className="text-gray-600 font-mono text-xs">
                  {judge.replace("groq/", "")}
                </span>
              </label>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Criteria</label>
          <div className="space-y-2">
            {DEFAULT_CRITERIA.map(c => (
              <label key={c} className="flex items-center gap-2 text-sm cursor-pointer">
                <input
                  type="checkbox"
                  checked={criteria.includes(c)}
                  onChange={() => toggleCriterion(c)}
                  className="rounded"
                />
                <span className="text-gray-600 capitalize">{c}</span>
              </label>
            ))}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <label className="text-sm font-medium text-gray-700">Samples per judge</label>
        <input
          type="range"
          min={1}
          max={5}
          value={nSamples}
          onChange={e => setNSamples(Number(e.target.value))}
          className="w-32"
        />
        <span className="text-sm text-gray-500">{nSamples}</span>
      </div>

      <div className="flex items-start gap-3">
        <label className="text-sm font-medium text-gray-700 mt-1 w-36 shrink-0">
          Temperatures
        </label>
        <div className="flex gap-3 flex-wrap">
          {TEMPERATURE_OPTIONS.map(t => (
            <label key={t} className="flex items-center gap-1.5 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={temperatures.includes(t)}
                onChange={() => toggleTemp(t)}
                className="rounded"
              />
              <span className="text-gray-600 font-mono text-xs">{t}</span>
            </label>
          ))}
        </div>
      </div>

      <button
        type="submit"
        disabled={loading || !prompt || !responseA || !responseB || judges.length === 0}
        className="w-full bg-gray-900 text-white py-3 rounded-lg text-sm font-medium hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
      >
        {loading ? "Running audit..." : "Run consistency audit"}
      </button>
    </form>
  )
}