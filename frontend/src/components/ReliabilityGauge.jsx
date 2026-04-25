export default function ReliabilityGauge({ score, ci }) {
  const color = score >= 80 ? "#16a34a" : score >= 60 ? "#d97706" : "#dc2626"
  const radius = 54
  const circumference = Math.PI * radius
  const progress = (score / 100) * circumference

  return (
    <div className="flex flex-col items-center">
      <svg width="140" height="80" viewBox="0 0 140 80">
        <path
          d={`M 16 70 A ${radius} ${radius} 0 0 1 124 70`}
          fill="none"
          stroke="#e5e7eb"
          strokeWidth="12"
          strokeLinecap="round"
        />
        <path
          d={`M 16 70 A ${radius} ${radius} 0 0 1 124 70`}
          fill="none"
          stroke={color}
          strokeWidth="12"
          strokeLinecap="round"
          strokeDasharray={`${progress} ${circumference}`}
        />
        <text
          x="70"
          y="65"
          textAnchor="middle"
          fontSize="22"
          fontWeight="600"
          fill={color}
        >
          {score}
        </text>
      </svg>
      <p className="text-xs text-gray-500 mt-1">
        95% CI: [{ci.lower}, {ci.upper}]
      </p>
    </div>
  )
}