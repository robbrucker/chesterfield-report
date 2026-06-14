---
name: chesterfield-report-design
description: Use this skill to generate well-branded interfaces and assets for The Chesterfield Report (a bioluminescent-cyberpunk hyperlocal news site for Chesterfield County, VA), either for production or throwaway prototypes/mocks. Contains essential design guidelines, colors, type, fonts, assets, and UI kit components for prototyping.
user-invocable: true
---

Read the `readme.md` file within this skill, and explore the other available files.

If creating visual artifacts (slides, mocks, throwaway prototypes, etc), copy assets out and create static HTML files for the user to view. If working on production code, you can copy assets and read the rules here to become an expert in designing with this brand.

If the user invokes this skill without any other guidance, ask them what they want to build or design, ask some questions, and act as an expert designer who outputs HTML artifacts _or_ production code, depending on the need.

## Quick map
- `styles.css` — link this one file to get every token + the webfonts.
- `tokens/` — colors, typography, spacing, effects, base (reset + `.cr-scanlines` / `.cr-grid-bg` / `.cr-kicker` utilities).
- `assets/` — `logo-mark.svg` (neon, primary) and `logo-mark-heritage.svg` (seal).
- `components/` — 12 React primitives (Button, IconButton, Input, Select, Checkbox, Switch, Badge, Tag, Card, Tabs, Toast, StatReadout). Load `_ds_bundle.js`, then `const { Button } = window.ChesterfieldReportDesignSystem_ad430c`.
- `ui_kits/report/` — full interactive news-site recreation to lift layout patterns from.
- `guidelines/` — foundation specimen cards.

## Non-negotiables (the brand in one breath)
- Deep teal-black surfaces; **neon teal `#22f5d4`** is the one primary signal. Magenta = breaking/live, amber = civic, lime = fresh.
- Type: **Chakra Petch** headlines · **Public Sans** body · **Space Mono** for ALL data, timestamps, kickers, labels (UPPERCASE, wide tracking, `//` prefix on eyebrows).
- Crisp corners, hairline borders, neon glow on hover/focus, scanline + grid textures. Cool/dark imagery only.
- Plain, fact-first civic copy. Numbers as receipts. **No emoji. No clickbait.**
- Motion is restrained (ticker, live pulse, radar sweep) and respects `prefers-reduced-motion`.
