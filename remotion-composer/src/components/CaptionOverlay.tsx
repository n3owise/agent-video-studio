import React, { Fragment } from "react";
import {
  AbsoluteFill,
  Sequence,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

// Word-level caption for TikTok-style highlight display
export interface WordCaption {
  word: string;
  startMs: number;
  endMs: number;
  // Force a page break after this word (e.g. sentence or scene boundaries).
  // Useful for CJK captions where pages should align with clause boundaries.
  pageBreakAfter?: boolean;
}

type CaptionOverlayProps = {
  words: WordCaption[];
  // How many words to show at once in a "page"
  wordsPerPage?: number;
  fontSize?: number;
  color?: string;
  highlightColor?: string;
  backgroundColor?: string;
  fontFamily?: string;
  // Separator rendered between words. Space-delimited languages want the
  // default " "; CJK languages (no inter-word spacing) should pass "".
  wordSeparator?: string;
  // Base text direction. "auto" (default) picks RTL when most words of the
  // captions are Arabic/Hebrew/Persian/Urdu. Each word is an
  // inline-block, which the bidi algorithm treats as a neutral object, so
  // without an explicit direction RTL words are laid out left-to-right and
  // the sentence reads backwards.
  direction?: "ltr" | "rtl" | "auto";
  isVertical?: boolean;
};

// ---------------------------------------------------------------------------
// Dynamic Auto-Emoji Lookup Table
// ---------------------------------------------------------------------------
const EMOJI_MAP: Record<string, string> = {
  // money / dollar
  money: "💸", dollar: "💸", dollars: "💸", cash: "💸", rich: "💸", profit: "💸", revenue: "💸", cost: "💸", price: "💸", finance: "💸", billion: "💸", million: "💸",
  // world / earth / global
  world: "🌍", earth: "🌍", global: "🌍", globe: "🌍", planet: "🌍", international: "🌍",
  // nuclear / atom / physics
  nuclear: "⚛️", atom: "⚛️", atomic: "⚛️", physics: "⚛️", quantum: "⚛️", radiation: "⚛️",
  // bomb / war / blast
  bomb: "💥", war: "💥", blast: "💥", explode: "💥", explosion: "💥", boom: "💥", destroy: "💥", destruction: "💥", impact: "💥",
  // time / clock / history
  time: "⏳", clock: "⏳", history: "⏳", historical: "⏳", timeline: "⏳", hour: "⏳", hours: "⏳", minute: "⏳", second: "⏳", century: "⏳", year: "⏳", years: "⏳",
  // tech / robot / ai / compute
  tech: "🤖", technology: "🤖", robot: "🤖", robots: "🤖", ai: "🤖", compute: "🤖", computer: "🤖", algorithm: "🤖", machine: "🤖", software: "🤖",
  // fire / heat / burn
  fire: "🔥", heat: "🔥", burn: "🔥", burning: "🔥", hot: "🔥", flame: "🔥", flames: "🔥",
  // alert / warning / danger
  alert: "🚨", warning: "🚨", emergency: "🚨", urgent: "🚨", alarm: "🚨", panic: "🚨",
  // lock / secret / code
  lock: "🔒", locked: "🔒", secret: "🔒", secrets: "🔒", code: "🔒", coding: "🔒", secure: "🔒", security: "🔒", encrypt: "🔒", encrypted: "🔒", privacy: "🔒",
  // idea / light / future
  idea: "💡", light: "💡", future: "💡", bulb: "💡", smart: "💡", solve: "💡", insight: "💡", think: "💡", genius: "💡", vision: "💡",
  // coffee / cup / drink
  coffee: "☕", cup: "☕", drink: "☕", cafe: "☕", espresso: "☕", tea: "☕",
  // death / kill / danger
  death: "☠️", dead: "☠️", die: "☠️", dying: "☠️", kill: "☠️", killer: "☠️", killed: "☠️", danger: "☠️", dangerous: "☠️", poison: "☠️", fatal: "☠️", toxic: "☠️",
  // star / space / universe
  star: "✨", stars: "✨", space: "✨", universe: "✨", cosmic: "✨", galaxy: "✨", magic: "✨", celestial: "✨", shine: "✨",
  // speed / fast / rapid
  speed: "⚡", fast: "⚡", rapid: "⚡", quick: "⚡", quickly: "⚡", lightning: "⚡", flash: "⚡", velocity: "⚡", power: "⚡", rush: "⚡",
  // health / cure / bio
  health: "🧬", cure: "🧬", bio: "🧬", biology: "🧬", dna: "🧬", gene: "🧬", genetics: "🧬", medicine: "🧬", medical: "🧬", doctor: "🧬", vaccine: "🧬", virus: "🧬",
  // growth / up / surge
  growth: "📈", grow: "📈", up: "📈", surge: "📈", scale: "📈", increase: "📈", rise: "📈", rising: "📈", stonks: "📈", market: "📈", chart: "📈", expand: "📈",
};

export function getWordEmoji(rawWord: string): string | null {
  if (!rawWord) return null;
  const clean = rawWord.toLowerCase().replace(/[^a-z0-9]/g, "");
  if (EMOJI_MAP[clean]) {
    return EMOJI_MAP[clean];
  }
  for (const [key, emoji] of Object.entries(EMOJI_MAP)) {
    if (clean === key || (clean.length > 3 && clean.startsWith(key))) {
      return emoji;
    }
  }
  return null;
}

const RTL_CHAR = /[\u0590-\u08FF\uFB1D-\uFDFF\uFE70-\uFEFF]/;
const LTR_CHAR = /[A-Za-z\u00C0-\u024F\u0370-\u03FF\u0400-\u04FF]/;

function detectDirection(words: WordCaption[]): "ltr" | "rtl" {
  // Count words, not first letter: Arabic captions often open with a Latin
  // brand name ("OpenMontage يحوّل ...") and must still read right-to-left.
  let rtl = 0;
  let ltr = 0;
  for (const w of words) {
    if (RTL_CHAR.test(w.word)) rtl++;
    else if (LTR_CHAR.test(w.word)) ltr++;
  }
  return rtl > ltr ? "rtl" : "ltr";
}

interface CaptionPage {
  words: WordCaption[];
  startMs: number;
  endMs: number;
}

function buildPages(words: WordCaption[], wordsPerPage: number): CaptionPage[] {
  const pages: CaptionPage[] = [];
  let pageWords: WordCaption[] = [];
  const flush = () => {
    if (pageWords.length === 0) return;
    pages.push({
      words: pageWords,
      startMs: pageWords[0].startMs,
      endMs: pageWords[pageWords.length - 1].endMs,
    });
    pageWords = [];
  };
  for (const w of words) {
    pageWords.push(w);
    if (pageWords.length >= wordsPerPage || w.pageBreakAfter) flush();
  }
  flush();
  return pages;
}

const PageRenderer: React.FC<{
  page: CaptionPage;
  fontSize: number;
  color: string;
  highlightColor: string;
  backgroundColor: string;
  fontFamily: string;
  wordSeparator: string;
  direction: "ltr" | "rtl";
  isVertical: boolean;
}> = ({ page, fontSize, color, highlightColor, backgroundColor, fontFamily, wordSeparator, direction, isVertical }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const currentMs = page.startMs + (frame / fps) * 1000;

  // Spring entrance
  const entrance = spring({
    frame,
    fps,
    config: { damping: 18, stiffness: 120 },
  });

  return (
    <AbsoluteFill
      style={{
        justifyContent: "flex-end",
        alignItems: "center",
        paddingBottom: isVertical ? 220 : 80,
      }}
    >
      <div
        dir={direction}
        style={{
          direction,
          opacity: entrance,
          transform: `translateY(${interpolate(entrance, [0, 1], [20, 0])}px)`,
          backgroundColor,
          borderRadius: 14,
          padding: isVertical ? "16px 24px" : "14px 28px",
          maxWidth: isVertical ? "88%" : "80%",
          textAlign: "center",
        }}
      >
        <span
          style={{
            fontSize,
            fontWeight: 800,
            fontFamily,
            lineHeight: 1.4,
            whiteSpace: "pre-wrap",
          }}
        >
          {page.words.map((w, i) => {
            const wordStartFrame = Math.round(((w.startMs - page.startMs) / 1000) * fps);
            const isActive = w.startMs <= currentMs && w.endMs > currentMs;
            const isPast = w.endMs <= currentMs;
            const emoji = getWordEmoji(w.word);

            // Kinetic spring bounce for active word (Hormozi / MrBeast style)
            const wordSpring = spring({
              frame: frame - wordStartFrame,
              fps,
              config: { damping: 14, stiffness: 180 },
            });
            const activeScale = interpolate(wordSpring, [0, 1], [1.22, 1.05]);
            const scale = isActive ? activeScale : 1;

            return (
              <Fragment key={`${w.startMs}-${i}`}>
                <span
                  style={{
                    position: "relative",
                    display: "inline-block",
                    margin: "0 5px",
                    transform: `scale(${scale})`,
                    transformOrigin: "center bottom",
                    whiteSpace: "nowrap",
                    color: isActive ? highlightColor : isPast ? color : `${color}99`,
                    transition: "none", // CSS transitions forbidden in Remotion
                    textShadow: isActive
                      ? `0 0 24px ${highlightColor}88, 0 2px 6px rgba(0,0,0,0.6)`
                      : "0 2px 4px rgba(0,0,0,0.5)",
                  }}
                >
                  {/* Emoji Badge above or next to the active bouncing word */}
                  {isActive && emoji && (
                    <span
                      style={{
                        position: "absolute",
                        left: "50%",
                        bottom: "100%",
                        transform: `translateX(-50%) translateY(-6px) scale(${activeScale})`,
                        fontSize: "0.85em",
                        filter: "drop-shadow(0 2px 8px rgba(0,0,0,0.5))",
                        lineHeight: 1,
                        pointerEvents: "none",
                        zIndex: 10,
                      }}
                    >
                      {emoji}
                    </span>
                  )}
                  {w.word}
                </span>
                {i < page.words.length - 1 ? wordSeparator : ""}
              </Fragment>
            );
          })}
        </span>
      </div>
    </AbsoluteFill>
  );
};

export const CaptionOverlay: React.FC<CaptionOverlayProps> = ({
  words,
  wordsPerPage: propWordsPerPage,
  fontSize: propFontSize,
  color = "#F8FAFC",
  highlightColor = "#22D3EE",
  backgroundColor = "rgba(15, 23, 42, 0.75)",
  fontFamily = "Space Grotesk, Inter, system-ui, sans-serif",
  wordSeparator = " ",
  direction = "auto",
  isVertical: propIsVertical,
}) => {
  const { fps, width, height } = useVideoConfig();
  const isVertical = propIsVertical ?? (height > width);
  const wordsPerPage = propWordsPerPage ?? (isVertical ? 4 : 6);
  const fontSize = propFontSize ?? (isVertical ? 52 : 42);

  const pages = buildPages(words, wordsPerPage);
  const resolvedDirection =
    direction === "auto" ? detectDirection(words) : direction;

  return (
    <AbsoluteFill>
      {pages.map((page, i) => {
        const fromFrame = Math.round((page.startMs / 1000) * fps);
        const nextStart = pages[i + 1]?.startMs ?? page.endMs + 500;
        const duration = Math.max(
          1,
          Math.round(((nextStart - page.startMs) / 1000) * fps)
        );

        return (
          <Sequence key={i} from={fromFrame} durationInFrames={duration}>
            <PageRenderer
              page={page}
              fontSize={fontSize}
              color={color}
              highlightColor={highlightColor}
              backgroundColor={backgroundColor}
              fontFamily={fontFamily}
              wordSeparator={wordSeparator}
              direction={resolvedDirection}
              isVertical={isVertical}
            />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
