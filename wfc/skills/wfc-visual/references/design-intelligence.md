# Design Intelligence Reference

Practical reference for AI agents generating HTML visualizations. Combines curated industry palettes, font pairings, aesthetic directions, and design reasoning rules into a single lookup.

Read this file when the content has a clear domain (healthcare, fintech, gaming, etc.) or when you need a distinctive visual direction beyond generic dark-theme-with-blue-accents.

---

## 1. Industry Color Palettes

30 curated palettes from 96 industry-specific color systems. Each palette is tuned for its domain's psychological associations and user expectations.

**How to use:** Match the content domain to a palette. Set CSS custom properties from the palette values. The Primary color anchors the identity, Secondary provides depth, CTA drives action, Background sets the canvas, Text ensures readability, and Border provides structure.

| # | Industry | Primary | Secondary | CTA | Background | Text | Border | Notes |
|---|----------|---------|-----------|-----|------------|------|--------|-------|
| 1 | SaaS (General) | `#2563EB` | `#3B82F6` | `#F97316` | `#F8FAFC` | `#1E293B` | `#E2E8F0` | Trust blue + orange CTA contrast |
| 2 | E-commerce | `#059669` | `#10B981` | `#F97316` | `#ECFDF5` | `#064E3B` | `#A7F3D0` | Success green + urgency orange |
| 3 | Healthcare | `#0891B2` | `#22D3EE` | `#059669` | `#ECFEFF` | `#164E63` | `#A5F3FC` | Calm cyan + health green |
| 4 | Fintech/Crypto | `#F59E0B` | `#FBBF24` | `#8B5CF6` | `#0F172A` | `#F8FAFC` | `#334155` | Gold trust + purple tech (dark bg) |
| 5 | Creative Agency | `#EC4899` | `#F472B6` | `#06B6D4` | `#FDF2F8` | `#831843` | `#FBCFE8` | Bold pink + cyan accent |
| 6 | Gaming | `#7C3AED` | `#A78BFA` | `#F43F5E` | `#0F0F23` | `#E2E8F0` | `#4C1D95` | Neon purple + rose action (dark bg) |
| 7 | AI/Chatbot | `#7C3AED` | `#A78BFA` | `#06B6D4` | `#FAF5FF` | `#1E1B4B` | `#DDD6FE` | AI purple + cyan interactions |
| 8 | Developer Tool | `#1E293B` | `#334155` | `#22C55E` | `#0F172A` | `#F8FAFC` | `#475569` | Code dark + run green (dark bg) |
| 9 | Cybersecurity | `#00FF41` | `#0D0D0D` | `#FF3333` | `#000000` | `#E0E0E0` | `#1F1F1F` | Matrix green + alert red (dark bg) |
| 10 | Educational | `#4F46E5` | `#818CF8` | `#F97316` | `#EEF2FF` | `#1E1B4B` | `#C7D2FE` | Playful indigo + energetic orange |
| 11 | Financial Dashboard | `#0F172A` | `#1E293B` | `#22C55E` | `#020617` | `#F8FAFC` | `#334155` | Dark bg + green positive indicators |
| 12 | Analytics Dashboard | `#1E40AF` | `#3B82F6` | `#F59E0B` | `#F8FAFC` | `#1E3A8A` | `#DBEAFE` | Blue data + amber highlights |
| 13 | Portfolio | `#18181B` | `#3F3F46` | `#2563EB` | `#FAFAFA` | `#09090B` | `#E4E4E7` | Monochrome + blue accent |
| 14 | Productivity Tool | `#0D9488` | `#14B8A6` | `#F97316` | `#F0FDFA` | `#134E4A` | `#99F6E4` | Teal focus + action orange |
| 15 | Luxury Brand | `#1C1917` | `#44403C` | `#CA8A04` | `#FAFAF9` | `#0C0A09` | `#D6D3D1` | Premium black + gold accent |
| 16 | Restaurant | `#DC2626` | `#F87171` | `#CA8A04` | `#FEF2F2` | `#450A0A` | `#FECACA` | Appetizing red + warm gold |
| 17 | Real Estate | `#0F766E` | `#14B8A6` | `#0369A1` | `#F0FDFA` | `#134E4A` | `#99F6E4` | Trust teal + professional blue |
| 18 | News/Media | `#DC2626` | `#EF4444` | `#1E40AF` | `#FEF2F2` | `#450A0A` | `#FECACA` | Breaking red + link blue |
| 19 | Social Media | `#E11D48` | `#FB7185` | `#2563EB` | `#FFF1F2` | `#881337` | `#FECDD3` | Vibrant rose + engagement blue |
| 20 | Climate Tech | `#059669` | `#10B981` | `#FBBF24` | `#ECFDF5` | `#064E3B` | `#A7F3D0` | Nature green + solar gold |
| 21 | Sustainability | `#059669` | `#10B981` | `#0891B2` | `#ECFDF5` | `#064E3B` | `#A7F3D0` | Nature green + ocean blue |
| 22 | Music Streaming | `#1E1B4B` | `#4338CA` | `#22C55E` | `#0F0F23` | `#F8FAFC` | `#312E81` | Dark audio + play green (dark bg) |
| 23 | B2B Service | `#0F172A` | `#334155` | `#0369A1` | `#F8FAFC` | `#020617` | `#E2E8F0` | Professional navy + blue CTA |
| 24 | Consulting | `#0F172A` | `#334155` | `#CA8A04` | `#F8FAFC` | `#020617` | `#E2E8F0` | Authority navy + premium gold |
| 25 | Legal | `#1E3A8A` | `#1E40AF` | `#B45309` | `#F8FAFC` | `#0F172A` | `#CBD5E1` | Authority navy + trust gold |
| 26 | Beauty/Spa | `#EC4899` | `#F9A8D4` | `#8B5CF6` | `#FDF2F8` | `#831843` | `#FBCFE8` | Soft pink + lavender luxury |
| 27 | Space Tech | `#F8FAFC` | `#94A3B8` | `#3B82F6` | `#0B0B10` | `#F8FAFC` | `#1E293B` | Star white + launch blue (dark bg) |
| 28 | Non-profit | `#0891B2` | `#22D3EE` | `#F97316` | `#ECFEFF` | `#164E63` | `#A5F3FC` | Compassion blue + action orange |
| 29 | Quantum Computing | `#00FFFF` | `#7B61FF` | `#FF00FF` | `#050510` | `#E0E0FF` | `#333344` | Quantum cyan + interference purple (dark bg) |
| 30 | Photography | `#18181B` | `#27272A` | `#F8FAFC` | `#000000` | `#FAFAFA` | `#3F3F46` | Pure black + white contrast (dark bg) |

### Palette CSS Template

Apply any palette by mapping its values to CSS custom properties:

```css
:root {
  --primary: #2563EB;      /* from Primary column */
  --secondary: #3B82F6;    /* from Secondary column */
  --cta: #F97316;          /* from CTA column */
  --bg: #F8FAFC;           /* from Background column */
  --text: #1E293B;         /* from Text column */
  --border: #E2E8F0;       /* from Border column */
  --surface: color-mix(in srgb, var(--bg) 85%, var(--primary) 15%);
  --text-dim: color-mix(in srgb, var(--text) 60%, var(--bg) 40%);
  --primary-dim: color-mix(in srgb, var(--primary) 12%, transparent 88%);
  --cta-dim: color-mix(in srgb, var(--cta) 12%, transparent 88%);
}
```

For dark-background palettes (Fintech, Gaming, Developer Tool, Cybersecurity, etc.), the light/dark theme logic inverts. The palette's Background becomes the dark theme default, and you derive a light variant by swapping to a light background with the same Primary.

---

## 2. Font Pairings

20 curated pairings from 57 options. Each includes a Google Fonts CSS import ready for `<style>` or `<link>` injection.

**How to use:** Pick the pairing that matches the content's feel. Copy the CSS import into your `<head>`. Set `--font-heading` and `--font-body` as CSS custom properties.

| # | Name | Heading Font | Body Font | Feel | Best For | CSS Import |
|---|------|-------------|-----------|------|----------|------------|
| 1 | Classic Elegant | Playfair Display | Inter | Luxury, editorial, timeless | Fashion, spa, high-end e-commerce, magazines | `@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@400;500;600;700&display=swap');` |
| 2 | Modern Professional | Poppins | Open Sans | Corporate, friendly, clean | SaaS, corporate, business apps, startups | `@import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@300;400;500;600;700&family=Poppins:wght@400;500;600;700&display=swap');` |
| 3 | Tech Startup | Space Grotesk | DM Sans | Innovative, bold, futuristic | Tech companies, AI products, startups | `@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');` |
| 4 | Developer Mono | JetBrains Mono | IBM Plex Sans | Technical, precise, functional | Developer tools, documentation, CLI apps | `@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');` |
| 5 | Geometric Modern | Outfit | Work Sans | Balanced, contemporary, versatile | Portfolios, agencies, landing pages | `@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Work+Sans:wght@300;400;500;600;700&display=swap');` |
| 6 | Luxury Serif | Cormorant | Montserrat | High-end, elegant, refined | Fashion brands, luxury e-commerce, jewelry | `@import url('https://fonts.googleapis.com/css2?family=Cormorant:wght@400;500;600;700&family=Montserrat:wght@300;400;500;600;700&display=swap');` |
| 7 | Bold Statement | Bebas Neue | Source Sans 3 | Impactful, dramatic, strong | Marketing sites, portfolios, event pages, sports | `@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Source+Sans+3:wght@300;400;500;600;700&display=swap');` |
| 8 | Wellness Calm | Lora | Raleway | Natural, relaxing, organic | Health apps, wellness, spa, meditation | `@import url('https://fonts.googleapis.com/css2?family=Lora:wght@400;500;600;700&family=Raleway:wght@300;400;500;600;700&display=swap');` |
| 9 | Brutalist Raw | Space Mono | Space Mono | Raw, technical, minimal, stark | Brutalist designs, developer portfolios, tech art | `@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&display=swap');` |
| 10 | Fashion Forward | Syne | Manrope | Avant-garde, creative, edgy | Fashion brands, art galleries, design studios | `@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@300;400;500;600;700&family=Syne:wght@400;500;600;700&display=swap');` |
| 11 | Dashboard Data | Fira Code | Fira Sans | Analytical, precise, data-driven | Dashboards, analytics, admin panels | `@import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=Fira+Sans:wght@300;400;500;600;700&display=swap');` |
| 12 | Magazine Style | Libre Bodoni | Public Sans | Editorial, refined, print-like | Magazines, online publications, journalism | `@import url('https://fonts.googleapis.com/css2?family=Libre+Bodoni:wght@400;500;600;700&family=Public+Sans:wght@300;400;500;600;700&display=swap');` |
| 13 | Crypto/Web3 | Orbitron | Exo 2 | Futuristic, blockchain, digital | Crypto platforms, NFT, Web3, blockchain | `@import url('https://fonts.googleapis.com/css2?family=Exo+2:wght@300;400;500;600;700&family=Orbitron:wght@400;500;600;700&display=swap');` |
| 14 | Gaming Bold | Russo One | Chakra Petch | Action, competitive, energetic | Gaming, esports, action, competitive sports | `@import url('https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@300;400;500;600;700&family=Russo+One&display=swap');` |
| 15 | Corporate Trust | Lexend | Source Sans 3 | Accessible, professional, clean | Enterprise, government, healthcare, finance | `@import url('https://fonts.googleapis.com/css2?family=Lexend:wght@300;400;500;600;700&family=Source+Sans+3:wght@300;400;500;600;700&display=swap');` |
| 16 | Financial Trust | IBM Plex Sans | IBM Plex Sans | Trustworthy, corporate, serious | Banks, finance, insurance, investment | `@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap');` |
| 17 | Academic | Crimson Pro | Atkinson Hyperlegible | Scholarly, accessible, educational | Universities, research, academic journals | `@import url('https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:wght@400;700&family=Crimson+Pro:wght@400;500;600;700&display=swap');` |
| 18 | Startup Bold | Outfit | Rubik | Confident, dynamic, innovative | Startups, pitch decks, product launches | `@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&family=Rubik:wght@300;400;500;600;700&display=swap');` |
| 19 | Accessibility First | Atkinson Hyperlegible | Atkinson Hyperlegible | Inclusive, WCAG, clear, legible | Government, healthcare, accessibility-critical | `@import url('https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:wght@400;700&display=swap');` |
| 20 | Neubrutalist Bold | Lexend Mega | Public Sans | Gen Z, loud, geometric, quirky | Neubrutalist designs, Gen Z brands, bold marketing | `@import url('https://fonts.googleapis.com/css2?family=Lexend+Mega:wght@100..900&family=Public+Sans:wght@100..900&display=swap');` |

### Font CSS Template

```css
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=DM+Sans:wght@400;500;700&display=swap');

:root {
  --font-heading: 'Space Grotesk', system-ui, sans-serif;
  --font-body: 'DM Sans', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', 'SF Mono', Consolas, monospace;
}

h1, h2, h3, h4, h5, h6 { font-family: var(--font-heading); }
body { font-family: var(--font-body); }
code, pre, .mono { font-family: var(--font-mono); }
```

---

## 3. Aesthetic Directions

9 visual approaches for HTML visualizations. Each direction defines a mood, visual strategy, and recommended palette/font combinations.

### 3.1 Monochrome Terminal

**Visual approach:** Green or amber text on black background. Everything in monospace. Borders are single-pixel solid lines or ASCII box-drawing characters. No gradients, no rounded corners. Cursor blink animation on focal element. Scanline overlay (optional).

**When to use:** Developer tools, cybersecurity content, CLI documentation, system architecture for engineering audiences.

**Recommended palettes:** Cybersecurity (#9), Developer Tool (#8), Financial Dashboard (#11).

**Recommended fonts:** Brutalist Raw (#9), Developer Mono (#4), Dashboard Data (#11).

**Key CSS:**
```css
:root {
  --bg: #000000;
  --text: #00FF41;
  --border: #00FF4133;
  --font-body: 'Space Mono', monospace;
}
body { background: #000; color: var(--text); font-family: var(--font-body); }
* { border-radius: 0 !important; }
```

### 3.2 Editorial

**Visual approach:** Serif headlines with generous whitespace. Muted, warm palette. Large type sizes. Subtle horizontal rules as section dividers. Think print magazine layout translated to screen. Pull quotes as accent elements.

**When to use:** Content-heavy explanations, documentation, blog-like technical writing, team communications, project recaps.

**Recommended palettes:** Portfolio (#13), B2B Service (#23), Consulting (#24).

**Recommended fonts:** Classic Elegant (#1), Magazine Style (#12), Luxury Serif (#6).

**Key CSS:**
```css
body { max-width: 720px; margin: 0 auto; line-height: 1.8; }
h1 { font-size: 2.5rem; font-weight: 400; letter-spacing: -0.02em; }
hr { border: none; border-top: 1px solid var(--border); margin: 3rem 0; }
```

### 3.3 Blueprint

**Visual approach:** Technical drawing feel. Fine grid background (light blue or white lines on dark blue). Precise measurements and annotations. Dotted connector lines. Small, precise labels. Monospace for all measurements and specs.

**When to use:** Architecture diagrams, system specifications, infrastructure layouts, database schemas, network topology.

**Recommended palettes:** Analytics Dashboard (#12), SaaS General (#1), Space Tech (#27).

**Recommended fonts:** Developer Mono (#4), Dashboard Data (#11), Tech Startup (#3).

**Key CSS:**
```css
body {
  background: #1e3a5a;
  background-image:
    linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px);
  background-size: 20px 20px;
  color: #e0f0ff;
}
.annotation { font-size: 10px; text-transform: uppercase; letter-spacing: 2px; }
```

### 3.4 Neon Dashboard

**Visual approach:** Saturated accent colors on deep dark background (near-black). Glowing borders via box-shadow. Subtle glassmorphism on cards. High contrast data. Animated pulse on live/active elements.

**When to use:** Real-time dashboards, monitoring, metrics, gaming stats, fintech data, crypto.

**Recommended palettes:** Fintech/Crypto (#4), Gaming (#6), Quantum Computing (#29), Music Streaming (#22).

**Recommended fonts:** Crypto/Web3 (#13), Gaming Bold (#14), Dashboard Data (#11).

**Key CSS:**
```css
:root { --bg: #0a0a1a; --glow: #7c3aed; }
.card {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(124,58,237,0.3);
  box-shadow: 0 0 20px rgba(124,58,237,0.1), inset 0 1px 0 rgba(255,255,255,0.05);
  backdrop-filter: blur(12px);
}
```

### 3.5 Paper/Ink

**Visual approach:** Warm cream/off-white background. Dark brown/charcoal text. Subtle paper texture via CSS noise. Thin ink-like borders. Hand-drawn feel where possible. Mermaid `handDrawn` mode pairs well.

**When to use:** Informal explanations, brainstorming sessions, sketch-phase architecture, team retrospectives, mind maps.

**Recommended palettes:** Luxury Brand (#15), Portfolio (#13), Photography (#30).

**Recommended fonts:** Wellness Calm (#8), Academic (#17), Classic Elegant (#1).

**Key CSS:**
```css
:root {
  --bg: #faf8f3;
  --text: #2c2416;
  --border: #d4c5a9;
  --ink: #3d3425;
}
body {
  background: var(--bg);
  background-image: url("data:image/svg+xml,%3Csvg width='4' height='4' xmlns='http://www.w3.org/2000/svg'%3E%3Crect width='1' height='1' fill='%23d4c5a920'/%3E%3C/svg%3E");
}
```

### 3.6 Hand-Drawn / Sketch

**Visual approach:** Wiggly lines, informal whiteboard feel. Mermaid `look: 'handDrawn'` for diagrams. Rounded, slightly irregular shapes. Comic-style annotations. Informal font choices.

**When to use:** Early-stage design, whiteboard sessions, conceptual diagrams, brainstorming outputs, team alignment visuals.

**Recommended palettes:** Educational (#10), Creative Agency (#5), Non-profit (#28).

**Recommended fonts:** Geometric Modern (#5), Wellness Calm (#8), Modern Professional (#2).

**Mermaid config:**
```javascript
mermaid.initialize({
  startOnLoad: true,
  theme: 'base',
  look: 'handDrawn',
  layout: 'elk',
  themeVariables: { /* match page palette */ }
});
```

### 3.7 IDE-Inspired

**Visual approach:** Borrow a real editor color scheme (Dracula, Nord, Catppuccin, Solarized, Gruvbox, One Dark). Syntax-colored elements. Tab-like navigation. File-tree sidebars. Status bar footer.

**When to use:** Code reviews, diff visualizations, API documentation, developer-facing content, technical architecture for engineers.

**Recommended palettes:** Developer Tool (#8), Financial Dashboard (#11), Cybersecurity (#9).

**Recommended fonts:** Developer Mono (#4), Brutalist Raw (#9), Dashboard Data (#11).

**Example (Dracula):**
```css
:root {
  --bg: #282a36;
  --surface: #44475a;
  --text: #f8f8f2;
  --comment: #6272a4;
  --cyan: #8be9fd;
  --green: #50fa7b;
  --orange: #ffb86c;
  --pink: #ff79c6;
  --purple: #bd93f9;
  --red: #ff5555;
  --yellow: #f1fa8c;
}
```

### 3.8 Data-Dense

**Visual approach:** Small type (12-13px body), tight spacing, maximum information density. Tabular layouts. Minimal decoration. Monospace numbers. Heat map colors for severity/status. Designed for power users who want all the data.

**When to use:** Audit reports, comparison matrices, feature inventories, benchmark results, review dashboards, status boards.

**Recommended palettes:** Analytics Dashboard (#12), Financial Dashboard (#11), B2B Service (#23).

**Recommended fonts:** Dashboard Data (#11), Financial Trust (#16), Developer Mono (#4).

**Key CSS:**
```css
body { font-size: 13px; line-height: 1.4; }
.data-cell { padding: 6px 10px; font-variant-numeric: tabular-nums; }
th { font-size: 10px; text-transform: uppercase; letter-spacing: 1.5px; }
```

### 3.9 Gradient Mesh

**Visual approach:** Bold gradients as backgrounds. Glassmorphism cards with backdrop-filter blur. Modern SaaS feel. Rounded corners (16-24px). Vibrant accent colors. Smooth transitions. Feels like a premium marketing page.

**When to use:** Product showcases, feature announcements, executive summaries, stakeholder presentations, landing page prototypes.

**Recommended palettes:** SaaS General (#1), AI/Chatbot (#7), Creative Agency (#5), Educational (#10).

**Recommended fonts:** Tech Startup (#3), Modern Professional (#2), Startup Bold (#18), Geometric Modern (#5).

**Key CSS:**
```css
body {
  background: #0f172a;
  background-image:
    radial-gradient(at 20% 30%, rgba(99,102,241,0.3) 0%, transparent 50%),
    radial-gradient(at 80% 70%, rgba(236,72,153,0.2) 0%, transparent 50%),
    radial-gradient(at 50% 50%, rgba(6,182,212,0.15) 0%, transparent 60%);
}
.glass-card {
  background: rgba(255,255,255,0.06);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 20px;
}
```

---

## 4. Design Reasoning Rules

25 trigger-to-pattern rules for selecting the right visual approach. When the content matches a trigger, apply the recommended pattern.

| # | Trigger | Recommended Pattern | Palette | Font Pairing | Key Details |
|---|---------|-------------------|---------|--------------|-------------|
| 1 | Trust-dependent sector (banking, insurance, legal, government) | Trust & Authority + Minimalism | Consulting (#24), Legal (#25), B2B Service (#23) | Corporate Trust (#15), Financial Trust (#16) | Navy/blue primary, gold accents, serif or clean sans, credentials prominent, no playful elements |
| 2 | Data-heavy platform (analytics, dashboards, monitoring) | Data-Dense + Heat Maps | Analytics Dashboard (#12), Financial Dashboard (#11) | Dashboard Data (#11), Developer Mono (#4) | Small type, tabular layouts, cool-to-hot gradients, real-time pulse, monospace numbers |
| 3 | Engagement-focused (social, creator, community) | Vibrant + Motion-Driven | Social Media (#19), Creative Agency (#5) | Fashion Forward (#10), Modern Professional (#2) | Saturated colors, bold typography, scroll animations, engagement counters |
| 4 | Healthcare / Medical | Calming Cyans + Accessible | Healthcare (#3) | Accessibility First (#19), Corporate Trust (#15) | WCAG AAA, 4.5:1+ contrast, no neon, no aggressive motion, clear hierarchy, large touch targets (44px+) |
| 5 | Fintech / Crypto | Dark Mode + Trust Indicators | Fintech/Crypto (#4), Financial Dashboard (#11) | Crypto/Web3 (#13), Financial Trust (#16) | Dark backgrounds, real-time number animations, security badges, gold/green for positive, red for alerts |
| 6 | Gaming / Esports | Neon/Dark + Bold Typography | Gaming (#6), Quantum Computing (#29) | Gaming Bold (#14), Crypto/Web3 (#13) | Deep dark background, neon accents with glow, aggressive typography, WebGL/3D optional, high energy |
| 7 | Developer tools / CLI | Terminal Aesthetic + Monospace | Developer Tool (#8), Cybersecurity (#9) | Developer Mono (#4), Brutalist Raw (#9) | Dark syntax-themed backgrounds, monospace everywhere, keyboard shortcuts, code examples, command palette UX |
| 8 | E-commerce / Conversion | Feature-Rich + Urgency | E-commerce (#2), Restaurant (#16) | Geometric Modern (#5), Modern Professional (#2) | Success green + urgency orange, card hover lift, clear CTAs, product imagery focus, price prominence |
| 9 | Luxury / Premium | Storytelling + Slow Reveals | Luxury Brand (#15), Photography (#30) | Classic Elegant (#1), Luxury Serif (#6) | Black + gold, slow parallax (400-600ms), generous whitespace, serif headlines, high-quality imagery |
| 10 | Educational / Learning | Playful + Progress Indicators | Educational (#10) | Modern Professional (#2), Academic (#17) | Indigo/orange, progress bars, gamification elements, friendly typography, achievement badges |
| 11 | AI / Chatbot | Streaming Text + Minimal Chrome | AI/Chatbot (#7) | Tech Startup (#3), Geometric Modern (#5) | Purple primary, typing indicators, conversational UI, fade-in responses, minimal surrounding chrome |
| 12 | Sustainability / Climate | Organic Biophilic + Data Transparency | Climate Tech (#20), Sustainability (#21) | Wellness Calm (#8), Corporate Trust (#15) | Green earth tones, impact visualizations, progress indicators, no greenwashing, real data prominent |
| 13 | Music / Audio | Dark Mode + Waveform Visuals | Music Streaming (#22) | Fashion Forward (#10), Brutalist Raw (#9) | Near-black backgrounds, audio waveform accents, play-green CTA, album art colors as accents |
| 14 | Real Estate / Property | Hero Images + Map Integration | Real Estate (#17) | Modern Professional (#2), Corporate Trust (#15) | Teal/blue, professional feel, large property images, trust signals, virtual tour capability |
| 15 | News / Media | High Contrast + Breaking Alerts | News/Media (#18) | Magazine Style (#12), Corporate Trust (#15) | Red for breaking/urgent, blue for links, high contrast, mobile-first reading, clear category navigation |
| 16 | Portfolio / Personal | Storytelling + Unique Character | Portfolio (#13), Photography (#30) | Geometric Modern (#5), Fashion Forward (#10) | Monochrome base + one accent color, scroll-triggered reveals, case study format, unique aesthetic identity |
| 17 | Non-profit / Cause | Impact Stories + Donation Transparency | Non-profit (#28) | Wellness Calm (#8), Accessibility First (#19) | Compassion blue, action orange CTA, impact counters, story-driven layout, transparent financials |
| 18 | Cybersecurity / Threat | Matrix Aesthetic + Real-Time Alerts | Cybersecurity (#9) | Developer Mono (#4), Brutalist Raw (#9) | Pure black background, matrix green text, red for alerts, terminal feel, threat visualization |
| 19 | Architecture / System Diagrams | Blueprint + Precise Annotations | SaaS General (#1), Analytics Dashboard (#12) | Tech Startup (#3), Developer Mono (#4) | Grid background, precise labels, connection lines with arrowheads, component cards with typed borders |
| 20 | Executive / Stakeholder Summary | Gradient Mesh + Hero Numbers | SaaS General (#1), AI/Chatbot (#7) | Modern Professional (#2), Startup Bold (#18) | Bold KPI numbers, glassmorphism cards, gradient backgrounds, countUp animations, scannable layout |
| 21 | Space / Aerospace | Deep Dark + Precision Data | Space Tech (#27) | Tech Startup (#3), Crypto/Web3 (#13) | Near-black background, star-white text, metallic accents, telemetry displays, HUD-style overlays |
| 22 | Beauty / Wellness | Soft Pastels + Calming Motion | Beauty/Spa (#26), Healthcare (#3) | Wellness Calm (#8), Classic Elegant (#1) | Soft pinks/lavenders, neumorphic buttons, breathing animations, gentle transitions (200-300ms) |
| 23 | Legal / Compliance | Authority Navy + Document Structure | Legal (#25), Consulting (#24) | Corporate Trust (#15), Academic (#17) | Navy + gold, credential display, case results, formal hierarchy, serif for authority headings |
| 24 | Code Review / Diff Visualization | IDE-Inspired + Before/After | Developer Tool (#8) | Developer Mono (#4), Brutalist Raw (#9) | Syntax-themed backgrounds, red/green diff highlights, side-by-side panels, line numbers, file tree nav |
| 25 | Comparison / Audit Table | Data-Dense + Status Indicators | Analytics Dashboard (#12), B2B Service (#23) | Dashboard Data (#11), Financial Trust (#16) | Tabular layout, status badges (match/gap/warn), sticky headers, alternating rows, sortable columns |

---

## 5. Anti-Patterns

Common design mistakes to avoid when generating HTML visualizations.

### Color and Contrast

- **Low contrast text.** Never use gray text on gray background. Minimum 4.5:1 ratio for normal text, 3:1 for large text (18px+ bold or 24px+ regular). Test with a contrast checker.
- **Color-only information.** Never convey meaning through color alone. Always pair color with an icon, label, or pattern (e.g., use a checkmark icon with green, not just green).
- **AI purple/pink gradients on everything.** The purple-to-pink gradient has become a cliche for AI products. Only use it when the content is genuinely about AI and the audience expects it. For other domains, use the domain-appropriate palette.
- **Same palette every time.** If you used dark-blue-with-cyan-accents last time, use a different direction this time. Variation is the point.

### Typography

- **Defaulting to Inter/Roboto/Arial.** These are fallback fonts, not design choices. Always pick a distinctive pairing from the font table.
- **Same font size for everything.** Establish clear hierarchy: hero numbers (36px+), headings (24-32px), subheadings (18-20px), body (14-16px), labels (10-12px).
- **Body text without line-height.** Always set `line-height: 1.5` minimum for body text. For long-form content, use 1.6-1.75.
- **Full-width text on large screens.** Cap text blocks at `max-width: 75ch` or use a centered container at 720-900px max-width.

### Layout

- **Flat solid-color backgrounds.** They look dead. Add subtle gradients, dot grids, or radial glows. The background should feel like a space, not a void.
- **Equal visual weight everywhere.** Not everything is equally important. Use card depth tiers (hero > elevated > default > recessed) to signal hierarchy.
- **Overflow on mobile.** Always test at 375px width. Use `min-width: 0` on flex/grid children. Wrap tables in scrollable containers.
- **Using `display: flex` on `<li>` for marker positioning.** This creates anonymous flex items that overflow. Use absolute positioning for list markers instead (see css-patterns.md).

### Animation

- **Animating everything.** Limit to 1-2 animated elements per viewport. The rest should be static on load.
- **Using width/height/top/left for animation.** Only animate `transform` and `opacity`. Everything else triggers expensive layout recalculations.
- **Ignoring prefers-reduced-motion.** Always include `@media (prefers-reduced-motion: reduce)` that disables or minimizes all animation.
- **Linear easing.** Linear motion feels robotic. Use `ease-out` for entrances, `ease-in` for exits, and `ease-in-out` for continuous motion.
- **Animations longer than 500ms for UI elements.** Micro-interactions should be 150-300ms. Only hero reveals and major transitions warrant 400-600ms.

### Content

- **Using emoji as UI icons.** Emoji render differently across platforms and lack semantic meaning. Use SVG icons or CSS-drawn indicators.
- **Placeholder "Lorem ipsum" content.** Always use realistic sample data. Placeholder text makes the design impossible to evaluate for information hierarchy.
- **Missing alt text on images.** Every `<img>` needs descriptive alt text. Decorative images get `alt=""` and `role="presentation"`.
- **Breaking the squint test.** Blur your eyes and look at the page. If you cannot perceive hierarchy (what is most important, what is secondary, what is detail), the visual weight distribution is wrong.
- **Breaking the swap test.** If replacing your fonts and colors with a generic dark theme makes the page indistinguishable from a template, the design has no identity. Push further.

### Dark Mode

- **Dark mode as an afterthought.** Both themes should look intentional. Define both palettes in CSS custom properties from the start.
- **Light mode only for dark-bg palettes.** Palettes like Fintech, Gaming, and Developer Tool are designed dark-first. Forcing them into light mode loses their character.
- **White text on pure black.** `#FFFFFF` on `#000000` is too harsh. Use off-white (`#E6EDF3`, `#F8FAFC`) on near-black (`#0D1117`, `#0F172A`).

---

## 6. UX Quick Reference

Critical UX guidelines for every generated HTML page. These are non-negotiable.

### Color Contrast

| Element | Minimum Ratio | Example |
|---------|--------------|---------|
| Normal text (< 18px) | 4.5:1 | `#1E293B` on `#F8FAFC` = 12.6:1 |
| Large text (18px+ bold, 24px+ regular) | 3:1 | `#64748B` on `#F8FAFC` = 4.6:1 |
| UI components (borders, icons) | 3:1 | Border must be visible against background |
| Focus indicators | 3:1 | Focus ring must contrast with both element and background |

### Touch Targets

```css
/* Minimum interactive element size */
button, a, [role="button"], input, select {
  min-height: 44px;
  min-width: 44px;
}

/* Minimum spacing between adjacent targets */
.button-group { gap: 8px; }
```

### Animation

```css
/* Duration guidelines */
/* Micro-interactions (hover, toggle): 150-200ms */
/* Entrance animations (fade-in, slide): 250-350ms */
/* Complex transitions (page, modal): 300-500ms */
/* Hero reveals (splash, loading): 500-800ms */

/* Only animate compositable properties */
.animated {
  transition: transform 0.2s ease-out, opacity 0.2s ease-out;
  /* NEVER: transition: width, height, top, left, margin, padding */
}

/* Respect user preferences */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

### Typography

```css
/* Minimum body text */
body {
  font-size: 16px;        /* Never smaller for body */
  line-height: 1.5;       /* 1.5 minimum, 1.6-1.75 for long-form */
}

/* Readable line length */
p, li, dd {
  max-width: 75ch;        /* 65-75 characters per line */
}

/* Type scale (modular) */
/* 12px - labels, captions */
/* 14px - secondary text, table cells */
/* 16px - body text */
/* 18px - large body, subheadings */
/* 24px - section headings */
/* 32px - page headings */
/* 36-48px - hero numbers, display */
```

### Responsive Breakpoints

Test at these widths to cover the range of real devices:

| Breakpoint | Device | CSS |
|-----------|--------|-----|
| 375px | iPhone SE, small phones | Default (mobile-first) |
| 768px | iPad, tablets | `@media (min-width: 768px)` |
| 1024px | Small laptop, iPad Pro | `@media (min-width: 1024px)` |
| 1440px | Desktop, large laptop | `@media (min-width: 1440px)` |

```css
/* Mobile-first responsive pattern */
.container { padding: 16px; }
.grid { grid-template-columns: 1fr; }

@media (min-width: 768px) {
  .container { padding: 24px; }
  .grid { grid-template-columns: 1fr 1fr; }
}

@media (min-width: 1024px) {
  .container { padding: 32px; max-width: 1100px; margin: 0 auto; }
  .grid { grid-template-columns: repeat(3, 1fr); }
}
```

### Semantic HTML

```html
<!-- Use semantic elements, not div soup -->
<header>  <!-- Page header with nav -->
<nav>     <!-- Navigation -->
<main>    <!-- Primary content -->
<article> <!-- Self-contained content -->
<section> <!-- Thematic grouping -->
<aside>   <!-- Sidebar, related content -->
<footer>  <!-- Page footer -->

<!-- ARIA for custom interactive elements -->
<button aria-label="Close dialog">X</button>
<div role="tabpanel" aria-labelledby="tab-1">...</div>
<span role="status" aria-live="polite">3 results found</span>
```

### Checklist Before Delivery

1. **Squint test:** Blur eyes. Can you perceive hierarchy?
2. **Swap test:** Would a generic dark theme be indistinguishable? If yes, push the aesthetic.
3. **Both themes:** Toggle light/dark. Both should look intentional.
4. **No overflow:** Resize browser to 375px width. No horizontal scroll.
5. **Contrast check:** All text meets 4.5:1 minimum.
6. **Touch targets:** All interactive elements are at least 44x44px.
7. **Reduced motion:** Enable `prefers-reduced-motion` in DevTools. Page should still be usable.
8. **Font loads:** No FOIT (flash of invisible text). Fonts load with `display=swap`.
9. **No console errors:** Open DevTools console. Zero errors.
10. **Zoom controls:** Every Mermaid diagram has +/-/reset zoom buttons.
