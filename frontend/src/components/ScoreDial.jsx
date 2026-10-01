export function tier(score) {
  if (score >= 75) return "strong";
  if (score >= 55) return "good";
  if (score >= 35) return "partial";
  return "weak";
}

export default function ScoreDial({ score, size = 96 }) {
  const r = size / 2 - 7;
  const c = 2 * Math.PI * r;
  const off = c * (1 - Math.max(0, Math.min(100, score)) / 100);
  return (
    <div className={`dial ${tier(score)}`} style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-hidden="true">
        <circle className="dial-track" cx={size / 2} cy={size / 2} r={r} />
        <circle className="dial-arc" cx={size / 2} cy={size / 2} r={r}
          strokeDasharray={c} strokeDashoffset={off} transform={`rotate(-90 ${size / 2} ${size / 2})`} />
      </svg>
      <div className="dial-num" style={{ fontSize: size * 0.3 }}>
        {Math.round(score)}
        <small>/100</small>
      </div>
    </div>
  );
}
