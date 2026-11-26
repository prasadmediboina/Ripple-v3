export function Logo({ size = 26 }: { size?: number }) {
  return (
    <span className="inline-flex items-center gap-2 font-semibold tracking-tight">
      <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden>
        <circle cx="16" cy="16" r="3.5" fill="#4DA3FF" />
        <circle cx="16" cy="16" r="9" fill="none" stroke="#4DA3FF" strokeWidth="1.6" opacity=".7" />
        <circle cx="16" cy="16" r="14.2" fill="none" stroke="#4DA3FF" strokeWidth="1.2" opacity=".35" />
      </svg>
      <span className="text-lg">Ripple</span>
    </span>
  );
}
