---
name: web-design
description: "Design web artifacts: landing pages, prototypes, decks. Process-first design with 54 brand design systems (Stripe, Linear, Vercel, etc.)."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Design, Web, HTML, CSS, UI, UX, Prototype, Landing-Page, Design-Systems]
---

# Web Design

Design process for creating HTML artifacts (landing pages, prototypes, decks) plus a library of 54 real-world design systems.

## Quick Decision

| Need | Approach |
|------|----------|
| From-scratch design with no brand | Design process (below) + your taste |
| "Make it look like Stripe/Linear/Vercel" | Load template: `skill_view(name="web-design", file_path="templates/<site>.md")` |
| Formal design token spec file | Use `design-md` skill instead |

## Design Process

### 1. Start From Context, Not Vibes
Before designing, look for: brand docs, existing screenshots, repo components, design tokens, UI kits, prior mockups.

If a repo is available, inspect: theme files, token files, global stylesheets, component files.

### 2. Define the Design System
For each artifact, define: colors, type, spacing, radii, shadows, motion, component treatment, interaction rules.

### 3. Build the Artifact
- Single self-contained HTML file (CSS/JS embedded)
- Preserve prior versions for major revisions
- No unnecessary dependencies

### 4. Verify
- File exists at stated path
- HTML is complete
- Check for syntax issues
- If browser tools available: check console errors, inspect screenshots

### Anti-Slop Rules
Avoid: aggressive gradients, glassmorphism by default, emoji, generic SaaS cards, fake dashboards, stock-photo heroes, oversized rounded rects, rainbow palettes, vague labels.

### Variation Rules
Default to at least 3 options:
1. **Conservative** — closest to existing patterns
2. **Strong-fit** — best interpretation of the brief
3. **Divergent** — more novel, explores taste boundaries

### Typography
- Editorial: serif or humanist headline + restrained sans body
- Software/productivity: precise sans with strong numeric treatment
- Technical: mono accents only, not mono everywhere
- Deck: large, clear, high contrast

### Color
Use brand colors first. If none: define small system (neutrals, surface, ink, accent, danger/success). Prefer oklch for harmonious palettes.

### HTML/CSS/JS Standards
- CSS variables for tokens, CSS grid for layout
- Real focus/hover states, `prefers-reduced-motion` handling
- Responsive scaling, semantic HTML
- Mobile hit targets ≥ 44px

## Design System Library (54 Brands)

Organized by category. Load any template: `skill_view(name="web-design", file_path="templates/<site>.md")`

### AI & Machine Learning
claude, cohere, elevenlabs, minimax, mistral.ai, ollama, opencode.ai, replicate, runwayml, together.ai, voltagent, x.ai

### Developer Tools
cursor, expo, linear.app, lovable, mintlify, posthog, raycast, resend, sentry, supabase, superhuman, vercel, warp, zapier

### Infrastructure & Cloud
clickhouse, composio, hashicorp, mongodb, sanity, stripe

### Design & Productivity
airtable, cal, clay, figma, framer, intercom, miro, notion, pinterest, webflow

### Fintech & Crypto
coinbase, kraken, revolut, wise

### Enterprise & Consumer
airbnb, apple, bmw, ibm, nvidia, spacex, spotify, uber

### Choosing a Design
- **Developer tools:** Linear, Vercel, Supabase, Raycast, Sentry
- **Documentation:** Mintlify, Notion, Sanity, MongoDB
- **Marketing:** Stripe, Framer, Apple, SpaceX
- **Dark mode:** Linear, Cursor, ElevenLabs, Warp, Superhuman
- **Light/clean:** Vercel, Stripe, Notion, Cal.com
- **Playful:** PostHog, Figma, Lovable, Zapier, Miro
- **Premium:** Apple, BMW, Stripe, Superhuman, Revolut

### Font Substitution
| Proprietary | CDN Substitute | Character |
|-------------|----------------|-----------|
| Geist | Geist (Google Fonts) | Geometric |
| sohne-var (Stripe) | Source Sans 3 | Light elegance |
| Circular (Spotify) | DM Sans | Geometric, warm |
| Airbnb Cereal | DM Sans | Rounded, friendly |
| figmaSans | Inter | Clean humanist |
