import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig } from "remotion";

interface StatCardProps {
  stat: string;
  subtitle?: string;
  statFontSize?: number;
  subtitleFontSize?: number;
  color?: string;
  accentColor?: string;
  backgroundColor?: string;
  isVertical?: boolean;
}

export const StatCard: React.FC<StatCardProps> = ({
  stat,
  subtitle,
  statFontSize,
  subtitleFontSize,
  color = "#FFFFFF",
  accentColor = "#F59E0B",
  backgroundColor = "#1F2937",
  isVertical: propIsVertical,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const isVertical = propIsVertical ?? (height > width);

  const resolvedStatFontSize = statFontSize || (isVertical ? 88 : 128);
  const resolvedSubtitleFontSize = subtitleFontSize || (isVertical ? 28 : 36);

  const scale = spring({
    frame,
    fps,
    config: { damping: 12, stiffness: 120 },
    from: 0.8,
    to: 1,
  });

  const subtitleOpacity = spring({
    frame: frame - 8,
    fps,
    config: { damping: 20 },
  });

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        background: backgroundColor,
        padding: isVertical ? "40px 24px" : "60px 80px",
      }}
    >
      <div style={{ textAlign: "center", maxWidth: isVertical ? "92%" : "85%" }}>
        <div
          style={{
            transform: `scale(${scale})`,
            fontSize: resolvedStatFontSize,
            color: accentColor,
            fontFamily: "Inter, system-ui, sans-serif",
            fontWeight: 800,
            lineHeight: 1.1,
            wordBreak: "break-word",
          }}
        >
          {stat}
        </div>
        {subtitle && (
          <div
            style={{
              opacity: subtitleOpacity,
              fontSize: resolvedSubtitleFontSize,
              color,
              fontFamily: "Inter, system-ui, sans-serif",
              fontWeight: 400,
              marginTop: isVertical ? 12 : 16,
              lineHeight: 1.3,
            }}
          >
            {subtitle}
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
