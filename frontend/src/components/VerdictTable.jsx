export default function VerdictTable({ verdicts }) {
  const winnerColor = (w) => {
    if (w === "A") return "bg-blue-100 text-blue-700"
    if (w === "B") return "bg-green-100 text-green-700"
    return "bg-gray-100 text-gray-600"
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-gray-100">
            <th className="text-left py-2 px-3 font-medium text-gray-500">Judge</th>
            <th className="text-left py-2 px-3 font-medium text-gray-500">Temp</th>
            <th className="text-left py-2 px-3 font-medium text-gray-500">Order</th>
            <th className="text-left py-2 px-3 font-medium text-gray-500">Winner</th>
            <th className="text-left py-2 px-3 font-medium text-gray-500">Latency</th>
            <th className="text-left py-2 px-3 font-medium text-gray-500">Reasoning</th>
          </tr>
        </thead>
        <tbody>
          {verdicts.map((v, i) => (
            <tr key={i} className="border-b border-gray-50 hover:bg-gray-50">
              <td className="py-2 px-3 font-mono text-gray-600">
                {v.judge_model.replace("groq/", "")}
              </td>
              <td className="py-2 px-3 font-mono text-gray-400">{v.temperature}</td>
              <td className="py-2 px-3 text-gray-500">{v.order}</td>
              <td className="py-2 px-3">
                <span className={`px-2 py-0.5 rounded-full font-medium ${winnerColor(v.winner)}`}>
                  {v.winner}
                </span>
              </td>
              <td className="py-2 px-3 text-gray-500">{v.latency_ms}ms</td>
              <td className="py-2 px-3 text-gray-500 max-w-xs truncate">{v.reasoning}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}