/** Original (non-emoji) god symbols, served from /public/gods. Same look on every device, preview and PDF. */
export const GOD_IMAGES = [
  { id: "om", src: "/gods/om.svg", label: "Om" },
  { id: "ganesha", src: "/gods/ganesha.svg", label: "Ganesha" },
  { id: "trishul", src: "/gods/trishul.svg", label: "Shiva (Trishul)" },
  { id: "lotus", src: "/gods/lotus.svg", label: "Lakshmi (Lotus)" },
  { id: "krishna", src: "/gods/krishna.svg", label: "Krishna (Flute)" },
  { id: "ram", src: "/gods/ram.svg", label: "Ram (Bow)" },
  { id: "chakra", src: "/gods/chakra.svg", label: "Vishnu (Chakra)" },
  { id: "hanuman", src: "/gods/hanuman.svg", label: "Hanuman (Gada)" },
  { id: "shankh", src: "/gods/shankh.svg", label: "Shankh" },
  { id: "swastik", src: "/gods/swastik.svg", label: "Swastik" },
  { id: "diya", src: "/gods/diya.svg", label: "Diya" },
  { id: "kalash", src: "/gods/kalash.svg", label: "Kalash" },
] as const;

export const DEFAULT_GOD_SRC = "/gods/om.svg";

/** Old drafts saved an emoji — map them to the new images so nothing breaks. */
const LEGACY_EMOJI: Record<string, string> = {
  "🕉️": "/gods/om.svg", "🕉": "/gods/om.svg", "ॐ": "/gods/om.svg",
  "🐘": "/gods/ganesha.svg", "🔱": "/gods/trishul.svg", "🪷": "/gods/lotus.svg",
  "🪈": "/gods/krishna.svg", "🏹": "/gods/ram.svg", "🌀": "/gods/chakra.svg",
  "🙏": "/gods/hanuman.svg", "⚔️": "/gods/trishul.svg", "✨": "/gods/diya.svg",
  "卐": "/gods/swastik.svg",
};

/** Always returns an image src (data URL / path) for the chosen god symbol. */
export function resolveGodSrc(v?: string): string {
  if (!v) return DEFAULT_GOD_SRC;
  if (v.startsWith("data:") || v.startsWith("http") || v.startsWith("/")) return v;
  return LEGACY_EMOJI[v] || DEFAULT_GOD_SRC;
}

/** God symbol is shown unless the user explicitly unchecked it. */
export function isGodVisible(d: { showGodImage?: boolean }): boolean {
  return d.showGodImage !== false;
}
