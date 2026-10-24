import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig } from "remotion";

interface TextCardProps {
  text: string;
  fontSize?: number;
  color?: string;
  backgroundColor?: string;
  isVertical?: boolean;
}

export const TextCard: React.FC<TextCardProps> = ({
  text,
  fontSize: propFontSize,
  color = "#FFFFFF",
  backgroundColor = "#1F2937",
  isVertical: propIsVertical,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const isVertical = propIsVertical ?? (height > width);
  const fontSize = propFontSize || (isVertical ? 48 : 64);

  const opacity = spring({ frame, fps, config: { damping: 20 } });
  const scale = spring({
    frame,
    fps,
    config: { damping: 15, stiffness: 100 },
    from: 0.95,
    to: 1,
  });

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        background: backgroundColor,
        padding: isVertical ? "40px 32px" : "80px",
      }}
    >
      <div
        style={{
          opacity,
          transform: `scale(${scale})`,
          fontSize,
          color,
          fontFamily: "Inter, system-ui, sans-serif",
          fontWeight: 700,
          textAlign: "center",
          maxWidth: isVertical ? "92%" : "80%",
          lineHeight: 1.35,
          wordBreak: "break-word",
        }}
      >
        {text}
      </div>
    </AbsoluteFill>
  );
};
