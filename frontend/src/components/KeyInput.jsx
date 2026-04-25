import { useState } from "react"

export default function KeyInput({ onKeyChange }) {
  const [key, setKey] = useState("")
  const [visible, setVisible] = useState(false)

  function handleChange(e) {
    const val = e.target.value
    setKey(val)
    onKeyChange(val)
    if (val) sessionStorage.setItem("byok_key", val)
    else sessionStorage.removeItem("byok_key")
  }

  return (
    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
      <p className="text-xs font-medium text-yellow-800 mb-2">
        Optional — bring your own API key for non-Groq models
      </p>
      <div className="flex gap-2">
        <input
          type={visible ? "text" : "password"}
          value={key}
          onChange={handleChange}
          placeholder="sk-... or gsk_..."
          className="flex-1 text-sm border border-gray-200 rounded px-3 py-2 focus:outline-none focus:border-gray-400"
        />
        <button
          onClick={() => setVisible(!visible)}
          className="text-xs px-3 py-2 border border-gray-200 rounded hover:bg-gray-50"
        >
          {visible ? "Hide" : "Show"}
        </button>
      </div>
      <p className="text-xs text-yellow-700 mt-2">
        Key is used in-session only — never stored on our servers.
      </p>
    </div>
  )
}