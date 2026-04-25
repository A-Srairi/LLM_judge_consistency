import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell
} from "recharts"

export default function BiasChart({ positionalBias, interJudge }) {
  const data = [
    {
      name: "Flip rate",
      value: Math.round(positionalBias.flip_rate * 100),
      max: 100,
      bad: positionalBias.is_significant,
    },
    {
      name: "Judge disagreement",
      value: Math.round((1 - Math.max(0, interJudge.krippendorff_alpha)) * 100),
      max: 100,
      bad: interJudge.krippendorff_alpha < 0.4,
    },
  ]

  return (
    <ResponsiveContainer width="100%" height={160}>
      <BarChart data={data} layout="vertical" margin={{ left: 16, right: 32 }}>
        <CartesianGrid strokeDasharray="3 3" horizontal={false} />
        <XAxis type="number" domain={[0, 100]} tickFormatter={v => `${v}%`} fontSize={11} />
        <YAxis type="category" dataKey="name" fontSize={11} width={120} />
        <Tooltip formatter={v => `${v}%`} />
        <Bar dataKey="value" radius={4}>
          {data.map((entry, i) => (
            <Cell key={i} fill={entry.bad ? "#ef4444" : "#22c55e"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}