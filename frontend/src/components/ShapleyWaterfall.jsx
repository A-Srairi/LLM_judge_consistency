import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell, LabelList
} from "recharts"

export default function ShapleyWaterfall({ shapley }) {
  const data = Object.entries(shapley.per_criterion)
    .map(([name, value]) => ({
      name: name.charAt(0).toUpperCase() + name.slice(1),
      value: Math.round(value * 100),
      dominant: name === shapley.dominant_criterion,
    }))
    .sort((a, b) => b.value - a.value)

  return (
    <div>
      <p className="text-xs text-gray-500 mb-3">
        Share of inconsistency attributed to each criterion.
        Dominant: <span className="font-medium text-gray-700">{shapley.dominant_criterion}</span>
      </p>
      <ResponsiveContainer width="100%" height={160}>
        <BarChart data={data} margin={{ left: 8, right: 32 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="name" fontSize={11} />
          <YAxis tickFormatter={v => `${v}%`} fontSize={11} />
          <Tooltip formatter={v => `${v}%`} />
          <Bar dataKey="value" radius={4}>
            <LabelList dataKey="value" position="top" fontSize={11} formatter={v => `${v}%`} />
            {data.map((entry, i) => (
              <Cell key={i} fill={entry.dominant ? "#7c3aed" : "#a78bfa"} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}