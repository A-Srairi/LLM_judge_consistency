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