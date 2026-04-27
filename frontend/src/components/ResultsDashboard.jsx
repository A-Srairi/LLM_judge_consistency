import ReliabilityGauge from "./ReliabilityGauge"
import BiasChart from "./BiasChart"
import ShapleyWaterfall from "./ShapleyWaterfall"
import VerdictTable from "./VerdictTable"

export default function ResultsDashboard({ result }) {
  const winnerBadge = (w) => {
    if (w === "A") return "bg-blue-100 text-blue-700"
    if (w === "B") return "bg-green-100 text-green-700"
    return "bg-gray-100 text-gray-600"
  }

  return (
    <div className="space-y-6">

      {/* summary bar */}
      <div className="bg-white border border-gray-200 rounded-xl p-6">
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <p className="text-xs text-gray-500 mb-1">Overall winner</p>
            <span className={`text-lg font-semibold px-3 py-1 rounded-full ${winnerBadge(result.overall_winner)}`}>
              Response {result.overall_winner}
            </span>
            <p className="text-sm text-gray-500 mt-3 max-w-xl">{result.verdict_summary}</p>
          </div>
          <div className="text-right">
            <p className="text-xs text-gray-500 mb-1">Reliability score</p>
            <ReliabilityGauge
              score={result.reliability_score}
              ci={result.confidence_interval}
            />
          </div>
        </div>
      </div>

      {/* bias + shapley */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <h3 className="text-sm font-medium text-gray-700 mb-4">Bias indicators</h3>
          <BiasChart
            positionalBias={result.positional_bias}
            interJudge={result.inter_judge_agreement}
          />
          <div className="mt-3 grid grid-cols-2 gap-3 text-xs text-gray-500">
            <div>
              <span className="font-medium text-gray-700">McNemar p-value: </span>
              {result.positional_bias.mcnemar_pvalue}
            </div>
            <div>
              <span className="font-medium text-gray-700">Krippendorff α: </span>
              {result.inter_judge_agreement.krippendorff_alpha}
              <span className="ml-1 text-gray-400">
                ({result.inter_judge_agreement.interpretation})
              </span>
            </div>
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <h3 className="text-sm font-medium text-gray-700 mb-4">Inconsistency attribution (Shapley)</h3>
          <ShapleyWaterfall shapley={result.shapley_attribution} />
        </div>
      </div>

      {/* per criterion agreement */}
      <div className="bg-white border border-gray-200 rounded-xl p-6">
        <h3 className="text-sm font-medium text-gray-700 mb-4">Per-criterion agreement</h3>
        <div className="grid grid-cols-3 gap-4">
          {Object.entries(result.inter_judge_agreement.per_criterion).map(([criterion, alpha]) => {
            const color = alpha > 0.6 ? "text-green-600" : alpha > 0.3 ? "text-amber-600" : "text-red-500"
            return (
              <div key={criterion} className="bg-gray-50 rounded-lg p-4 text-center">
                <p className="text-xs text-gray-500 capitalize mb-1">{criterion}</p>
                <p className={`text-xl font-semibold ${color}`}>{alpha}</p>
                <p className="text-xs text-gray-400 mt-1">Krippendorff α</p>
              </div>
            )
          })}
        </div>
      </div>

      {/* per judge breakdown */}
      <div className="bg-white border border-gray-200 rounded-xl p-6">
        <h3 className="text-sm font-medium text-gray-700 mb-4">Per-judge voting pattern</h3>
        <div className="space-y-3">
          {[...new Set(result.verdicts.map(v => v.judge_model))].map(judge => {
            const judgeVerdicts = result.verdicts.filter(v => v.judge_model === judge)
            const counts = judgeVerdicts.reduce((acc, v) => {
              acc[v.winner] = (acc[v.winner] || 0) + 1
              return acc
            }, {})
            const total = judgeVerdicts.length
            const aCount = counts["A"] || 0
            const bCount = counts["B"] || 0
            const tieCount = counts["tie"] || 0
            const dominant = aCount > bCount ? "A" : bCount > aCount ? "B" : "tie"
            const consistency = Math.round((Math.max(aCount, bCount, tieCount) / total) * 100)

            return (
              <div key={judge} className="flex items-center gap-4">
                <span className="font-mono text-xs text-gray-500 w-48 shrink-0">
                  {judge.replace("groq/", "")}
                </span>
                <div className="flex-1 flex gap-1 h-6">
                  {aCount > 0 && (
                    <div
                      className="bg-blue-200 rounded flex items-center justify-center text-xs text-blue-700 font-medium"
                      style={{ width: `${(aCount / total) * 100}%` }}
                    >
                      A×{aCount}
                    </div>
                  )}
                  {bCount > 0 && (
                    <div
                      className="bg-green-200 rounded flex items-center justify-center text-xs text-green-700 font-medium"
                      style={{ width: `${(bCount / total) * 100}%` }}
                    >
                      B×{bCount}
                    </div>
                  )}
                  {tieCount > 0 && (
                    <div
                      className="bg-gray-200 rounded flex items-center justify-center text-xs text-gray-600 font-medium"
                      style={{ width: `${(tieCount / total) * 100}%` }}
                    >
                      tie×{tieCount}
                    </div>
                  )}
                </div>
                <span className="text-xs text-gray-400 w-20 text-right">
                  {consistency}% consistent
                </span>
              </div>
            )
          })}
        </div>
      </div>

      {/* temperature sensitivity */}
      {result.temperature_sensitivity && (
        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <h3 className="text-sm font-medium text-gray-700 mb-1">
            Temperature sensitivity
          </h3>
          <p className="text-xs text-gray-400 mb-4">
            Most stable: <span className="font-medium text-gray-600">
              {result.temperature_sensitivity.most_stable_judge?.replace("groq/", "")}
            </span>
            {" · "}
            Least stable: <span className="font-medium text-gray-600">
              {result.temperature_sensitivity.least_stable_judge?.replace("groq/", "")}
            </span>
          </p>

          {/* sensitivity scores */}
          <div className="space-y-3 mb-6">
            {Object.entries(result.temperature_sensitivity.per_judge_sensitivity).map(([judge, score]) => {
              const pct = Math.round(score * 100)
              const color = score < 0.1 ? "bg-green-400" : score < 0.2 ? "bg-amber-400" : "bg-red-400"
              return (
                <div key={judge} className="flex items-center gap-3">
                  <span className="font-mono text-xs text-gray-500 w-48 shrink-0">
                    {judge.replace("groq/", "")}
                  </span>
                  <div className="flex-1 bg-gray-100 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${color}`}
                      style={{ width: `${Math.max(pct, 2)}%` }}
                    />
                  </div>
                  <span className="text-xs text-gray-500 w-16 text-right">
                    {score} sensitivity
                  </span>
                </div>
              )
            })}
          </div>

          {/* verdict heatmap */}
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="text-left py-2 px-3 font-medium text-gray-500">Judge</th>
                  {Object.keys(
                    Object.values(result.temperature_sensitivity.verdict_heatmap)[0] || {}
                  ).map(temp => (
                    <th key={temp} className="text-center py-2 px-3 font-medium text-gray-500">
                      temp={temp}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {Object.entries(result.temperature_sensitivity.verdict_heatmap).map(([judge, temps]) => (
                  <tr key={judge} className="border-b border-gray-50">
                    <td className="py-2 px-3 font-mono text-gray-600">
                      {judge.replace("groq/", "")}
                    </td>
                    {Object.entries(temps).map(([temp, dist]) => {
                      const dominant = dist.A > dist.B && dist.A > dist.tie ? "A"
                        : dist.B > dist.A && dist.B > dist.tie ? "B"
                        : dist.tie > 0 ? "tie" : "split"
                      const bgColor = dominant === "A" ? "bg-blue-50 text-blue-700"
                        : dominant === "B" ? "bg-green-50 text-green-700"
                        : dominant === "tie" ? "bg-gray-50 text-gray-500"
                        : "bg-amber-50 text-amber-700"
                      return (
                        <td key={temp} className={`py-2 px-3 text-center rounded ${bgColor}`}>
                          <div className="font-medium">{dominant}</div>
                          <div className="text-gray-400 text-xs">
                            A:{Math.round(dist.A * 100)}% B:{Math.round(dist.B * 100)}%
                          </div>
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* verdict table */}
      <div className="bg-white border border-gray-200 rounded-xl p-6">
        <h3 className="text-sm font-medium text-gray-700 mb-4">
          Raw verdicts — {result.verdicts.length} total
        </h3>
        <VerdictTable verdicts={result.verdicts} />
      </div>

    </div>
  )
}