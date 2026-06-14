# The Chesterfield Report — Design System

A **bioluminescent-cyberpunk** design system for *The Chesterfield Report*, a hyperlocal news site covering Chesterfield County, Virginia. It takes the paper's civic mission — trustworthy, plain-language reporting on a real Virginia county — and skins it in a river-at-night HUD: deep teal-black surfaces, neon heron-teal signal, and heritage gold/green/rust tones lifted straight from the heron seal.

> **Direction chosen with the user:** *"River/heron nature — bioluminescent teals, fog, wetland greens"* over the dark teal base, balanced cyberpunk (a clear neon skin over a real news layout), with glow edges, scanlines, animated grid washes and monospace data readouts.

## Sources
- **Live site:** https://chesterfield-virginia.xyz/ — current production site (dark teal `#06141a`, heron seal, civic beats, "This Week" digest, topic filter, map, opinion). Used for information architecture, content beats and the heron motif.
- **Logo:** user-supplied heron seal SVG (`uploads/logo_file-*.svg`) → preserved as `assets/logo-mark-heritage.svg`. The user approved a redesign, so the primary mark is now the neon reinterpretation `assets/logo-mark.svg`.
- No codebase or Figma was provided; the cyberpunk visual language is an original interpretation grounded in the site's IA and the heron/river identity.

---

## CONTENT FUNDAMENTALS — how the Report writes

**Vibe:** a wired local desk. Civic seriousness with a low electric hum. It reads like a trustworthy county paper that happens to run on a neon terminal — never sci-fi cosplay, never clickbait.

- **Person & voice:** third-person, active. *"Supervisors approved…"* not *"It was approved…"*. The newsroom is "we" only in first-person notes (tip line, newsletter); stories themselves stay reportorial. Readers are "you" in calls-to-action ("Get This Week", "Saw something the county didn't announce?").
- **The fact first.** Declarative sentences, the decision up top, the drama second. Headlines state what happened: *"Supervisors clear 220-acre riverfront rezoning on a 4–1 vote."*
- **Numbers as receipts.** Vote counts (`4–1`), timestamps (`19:42`), dollar figures (`$1.9B`), acreage — always concrete, always in **Space Mono** with tabular figures. Data is a trust signal here, not decoration.
- **Casing:** sentence case for headlines and body. **UPPERCASE + wide tracking** only for mono kickers, labels, beats and timestamps (`// GROWTH & DEVELOPMENT`, `LIVE`, `MON`).
- **Kickers** lead with `//` (a terminal-comment tic) — `// This Week in Chesterfield`, `// The feed`. Used sparingly, as section eyebrows.
- **Local always.** Place names do the work: Midlothian, Chester, Hull Street, Route 10, Swift Creek, the Appomattox, Pocahontas Park, the courthouse. National-politics framing is avoided on local stories.
- **No emoji.** Anywhere. No clickbait ("you won't believe"), no hype, no exclamation points in headlines. Jargon always gets a plain-language gloss.
- **Tone examples:** *"The week, decoded."* · *"Everything the county decided, scheduled, or set in motion — one scan."* · *"No spam. Unsubscribe in one click. Reader-funded, ad-light."*

---

## VISUAL FOUNDATIONS

**Overall motif:** a county river at night rendered as a heads-up display. Dark teal-black water, bioluminescent teal as the living signal (the heron's glow), heritage tones as the warm anchor to a real place.

- **Color.** Base is a 7-step teal-black ink ramp (`--ink-900 #03090c` → `--ink-300 #2a6470`); `--ink-800 #06141a` matches the live site. Neon accents carry all signal: **teal `#22f5d4`** (primary — links, focus, the brand), **magenta `#ff2e88`** (breaking / live / danger), **amber `#ffd23f`** (civic gold, official), **lime `#8dff5e`** (fresh/positive data). Heritage tones from the seal — river-green `#1f6b53`, heritage-gold `#d8a23a`, heron-rust `#b5462f`, reed, fog — ground imagery and eco beats. Text is a teal-tinted neutral ramp (`--text-strong #eafff9` → `--text-faint`). Author against the **semantic aliases** (`--accent`, `--breaking`, `--civic`, `--surface-card`, `--text-heading`…), not raw scale values.
- **Type.** Three families: **Chakra Petch** (display — techno grotesk, squared terminals, tight leading, used for headlines), **Public Sans** (body — the U.S. government / USWDS civic typeface, grounding the cyber skin in real civic identity), **Space Mono** (all data readouts, timestamps, kickers, labels). Scale runs 11→80px; headlines track tight (`-0.02em`), mono labels track wide (`+0.12em`) and UPPERCASE.
- **Spacing & layout.** 8px base grid (`--space-1`…`--space-10`). Containers: narrow 42rem (article measure), base 64rem, wide 80rem, max 90rem. Layouts are two-column (feed + sticky sidebar) with a fixed, blurred header and a breaking-news ticker bar beneath it.
- **Corners.** Crisp. Cards use `--radius-sm` (4px); most HUD elements are 2–6px. Pills (`999px`) are reserved for tags/chips and toggle tracks. **No big friendly rounding** — the system reads sharp and instrument-like.
- **Borders.** Hairline `1px` dividers in `--ink-400`; `--ink-300` for stronger edges; a `3px` neon edge (`--bw-3`) for emphasis (accent bars, active rails, focus). Cards = hairline border + optional top accent bar in the tone color.
- **Backgrounds & texture.** Two signature textures: **scanlines** (`--tex-scanlines`, a subtle CRT overlay, ~40–70% opacity) and a **neon grid wash** (`--tex-grid` at 32px). "Photos" in mocks are duotone teal/violet gradients with the grid + scanline overlay, corner brackets and a mono caption — an honest, on-brand stand-in for real imagery (see Imagery below). The map view is a radar canvas with a sweeping conic gradient.
- **Shadows & glow.** Elevation shadows are cool and dark (`--shadow-sm/md/lg`, pure black alpha — never warm). The signature depth cue is **neon glow**: `--glow-md-teal/magenta/amber` = a 1px colored ring + a soft 18–22px colored bloom, used on hover, focus and active signal elements. Text glow (`--glow-text-*`) for big mono values and the drop-cap.
- **Imagery vibe.** Cool, nocturnal, duotone — teal/green for nature & civic, violet/magenta for incidents/roads. Grainy CRT feel via scanlines. The brand reads cold and luminous, never warm or sunny. (Real photography, when supplied, should be graded cool/dark to match.)
- **Borders vs gradients vs capsules.** Section eyebrows and labels sit on the surface directly (no chips); status uses **badges** (bordered wash capsules) and **tags** (pill chips). Protection gradients appear only over hero "photos" (bottom-up dark gradient for text legibility).
- **Motion.** Restrained and purposeful. Fast eased transitions (`--dur-fast 120ms` / `--dur-base 200ms`, `--ease-out`). Signature ambient loops: the **breaking ticker** marquee, the **live dot** pulse, the **map radar** sweep and **pin pings**. Everything respects `prefers-reduced-motion` (loops and transitions collapse). No bounces, no parallax, no decorative spinners.
- **Hover / press.** Hover = neon edge + glow appears, color lifts toward `--text-strong`, interactive cards lift `-2px`. Press = `translateY(1px)` (buttons) / settle back to 0 (cards). Focus = the `--ring` token (dark gap + teal ring + bloom). Links underline on hover with a 3px offset.

---

## ICONOGRAPHY
- **System:** a hand-rolled inline **Lucide-style** stroke set (`ui_kits/report/icons.js`, `window.CRIcons`) — 2px stroke, round caps/joins, 24px grid, currentColor. This is a **substitution**: the live site's exact icon set wasn't available. Swap in the official **Lucide** package (or the real set) to match production — the metrics already line up.
- **Usage:** icons are monochrome, inherit text/neon color, sized in `em`. Used in `IconButton`, inline meta rows (clock, map-pin), buttons (send, arrow), and the map legend. Stroke-only — no filled or duotone icons.
- **No emoji, ever.** A few **Unicode glyphs** appear as deliberate typographic marks: `//` for kickers, `▲ ▼ ·` for stat trend deltas, `×` for remove affordances, `–` (en dash) in vote counts.
- **Logo:** `assets/logo-mark.svg` (neon heron in a HUD frame) is primary; `assets/logo-mark-heritage.svg` (the original gold-ringed seal) is the heritage/print mark. The wordmark lockup pairs the neon mark with "The / Chesterfield Report" set in Chakra Petch.

---

## INDEX / MANIFEST

**Root**
- `styles.css` — global entry point (import this one file). `@import`s the token layer below.
- `readme.md` — this file. `SKILL.md` — Agent-Skill wrapper.

**`tokens/`** (all `@import`ed by `styles.css`)
- `fonts.css` — Google Fonts import (Chakra Petch / Public Sans / Space Mono). *See caveat.*
- `colors.css` · `typography.css` · `spacing.css` · `effects.css` · `base.css` (reset + texture utility classes `.cr-scanlines`, `.cr-grid-bg`, `.cr-kicker`).

**`assets/`** — `logo-mark.svg` (neon), `logo-mark-heritage.svg` (seal).

**`components/`** — 12 React primitives, grouped. Each has `<Name>.jsx`, `<Name>.d.ts`, a `.prompt.md` where useful, and one `@dsCard` HTML per directory.
- `buttons/` — **Button** (primary/secondary/ghost/danger/civic), **IconButton**
- `forms/` — **Input**, **Select**, **Checkbox**, **Switch**
- `labels/` — **Badge** (status/live), **Tag** (filter chips)
- `surface/` — **Card** (HUD panel: accent bar, gradient, corner bracket, hover lift)
- `navigation/` — **Tabs** (animated neon underline)
- `feedback/` — **Toast**
- `data/` — **StatReadout** (mono HUD counters)

Consume in card/kit HTML via `const { Button } = window.ChesterfieldReportDesignSystem_ad430c` after loading `_ds_bundle.js`.

**`ui_kits/report/`** — interactive recreation of the full news site (`index.html`). Screens: home feed, This Week digest, single article, topic filter, live map/radar, and the tip-line + newsletter. Files: `data.js`, `icons.js`, `parts.jsx` (StoryCard/ListRow/PhotoFrame/etc.), `Shell.jsx`, `HomeFeed.jsx`, `ThisWeek.jsx`, `Article.jsx`, `TopicFilter.jsx`, `MapView.jsx`, `TipSubmit.jsx`, `app.jsx`, `report.css`.

**`guidelines/`** — foundation specimen cards (Colors, Type, Spacing, Brand) shown in the Design System tab.

---

## CAVEATS / SUBSTITUTIONS
1. **Fonts are substitutions.** The live site's exact typefaces weren't available; Chakra Petch / Public Sans / Space Mono are intentional brand choices loaded from Google Fonts. Swap in licensed/self-hosted files if you have the real ones.
2. **Icons are a Lucide-style substitution** (see Iconography). Point at the production icon set to match exactly.
3. **The neon logo is a redesign** (user-approved). The heritage seal is preserved.
4. **"Photos" are gradient stand-ins** — no real photography was available. Drop in real images (graded cool/dark) where the `PhotoFrame` placeholders sit.
