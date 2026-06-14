# Install in Claude Code

This folder **is** a Claude Code Agent Skill — the whole Chesterfield Report design system. Drop it in and Claude Code can design in-brand (HTML mocks or production code).

## Install (drop-in)

1. Unzip this package.
2. Move the folder into your repo so it lands here, named for the skill ID:
   ```
   <your-repo>/.claude/skills/chesterfield-report-design/
   ```
   (The folder must contain `SKILL.md` at its top level. Rename the unzipped folder to `chesterfield-report-design` if needed.)
3. Restart / reopen Claude Code in that repo. The skill auto-registers from `SKILL.md` (`name: chesterfield-report-design`, `user-invocable: true`).

## Use it

- Invoke explicitly: *"Use the chesterfield-report-design skill to build a press-release page."*
- Or just describe the work — Claude reads `readme.md` + the token CSS and designs in-brand.

## What Claude Code reads first

- `readme.md` — full brand guide (voice, color, type, motion, iconography, manifest).
- `styles.css` — link this one file to inherit every token + the webfonts.
- `components/` — 12 React primitives. Load `_ds_bundle.js`, then `const { Button } = window.ChesterfieldReportDesignSystem_ad430c`.
- `ui_kits/report/` — full interactive news-site recreation to lift layout patterns from.
- `assets/` — `logo-mark.svg` (neon, primary), `logo-mark-heritage.svg` (seal).

## Before production

- **Fonts** (Chakra Petch / Public Sans / Space Mono) and the **Lucide-style icons** are intentional substitutions loaded from CDNs. Swap in your licensed/self-hosted files — metrics already line up. See CAVEATS in `readme.md`.
- `_ds_bundle.js`, `_ds_manifest.json`, `_adherence.oxlintrc.json` are auto-generated; treat them as build artifacts.
