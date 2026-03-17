interface GradeBadgeProps {
  grade: string;
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
}

const GRADE_CONFIG: Record<string, { bg: string; text: string; label: string }> = {
  S: { bg: "bg-amber-500/20", text: "text-amber-400", label: "Exceptional" },
  A: { bg: "bg-green-500/20", text: "text-green-400", label: "Excellent" },
  B: { bg: "bg-blue-500/20", text: "text-blue-400", label: "Good" },
  C: { bg: "bg-yellow-500/20", text: "text-yellow-400", label: "Adequate" },
  D: { bg: "bg-orange-500/20", text: "text-orange-400", label: "Poor" },
  F: { bg: "bg-red-500/20", text: "text-red-400", label: "Failing" },
};

const SIZE_CLASSES = {
  sm: "h-6 w-6 text-xs",
  md: "h-8 w-8 text-sm",
  lg: "h-12 w-12 text-lg",
};

export function GradeBadge({ grade, size = "md", showLabel = false }: GradeBadgeProps) {
  const fallback = { bg: "bg-red-500/20", text: "text-red-400", label: "Failing" };
  const config = GRADE_CONFIG[grade] ?? fallback;

  return (
    <div className="inline-flex items-center gap-2">
      <span
        className={`inline-flex items-center justify-center rounded-full font-bold ${config.bg} ${config.text} ${SIZE_CLASSES[size]}`}
      >
        {grade}
      </span>
      {showLabel && (
        <span className={`text-sm ${config.text}`}>{config.label}</span>
      )}
    </div>
  );
}
