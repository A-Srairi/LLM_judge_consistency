import { useState } from "react"
import axios from "axios"

const API_BASE = "http://127.0.0.1:8000"

export function useAudit() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)

  async function runAudit(formData, apiKey) {
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const headers = { "Content-Type": "application/json" }
      if (apiKey) headers["X-Api-Key"] = apiKey

      const payload = {
        prompt: formData.prompt,
        response_a: formData.response_a,
        response_b: formData.response_b,
        judges: formData.judges,
        criteria: formData.criteria,
        n_samples: formData.n_samples,
      }

      const response = await axios.post(`${API_BASE}/audit`, payload, { headers })
      setResult(response.data)
    } catch (err) {
      setError(
        err.response?.data?.detail || err.message || "Something went wrong."
      )
    } finally {
      setLoading(false)
    }
  }

  function reset() {
    setResult(null)
    setError(null)
  }

  return { loading, error, result, runAudit, reset }
}