# WFC Logo Assets

Professional SVG logos for the World Fucking Class multi-agent framework.

## 🏆 Championship Belt Logos (PRIMARY BRANDING)

**The official WFC logo - Championship Belt style representing world-class code review mastery.**

### 1. Championship Belt Full (`logo-championship-belt.svg`)

**800x300px** - Full championship belt with crown, laurel wreaths, and agent iconography

**Design elements:**

- Gold metallic championship belt with ornate detailing
- Purple-cyan gradient WFC text (brand colors)
- Crown at top (world-class excellence)
- Laurel wreaths (victory/achievement)
- Hexagonal network pattern (54 expert agents)
- Side plates with "MULTI AGENT CODE REVIEW" and "CONSENSUS DRIVEN QUALITY ASSURED"
- "54 EXPERT AGENTS" badge

**Use for:**

- README hero section
- Documentation homepage
- Marketing materials
- Conference presentations
- GitHub social preview
- Website hero/banner

**Symbolism:**

- **Championship belt**: World-class achievement, mastery, excellence
- **Gold metallic**: Premium quality, industry leadership
- **Crown**: Supreme authority in code review
- **Laurel wreaths**: Victory over code quality issues
- **Hexagons**: Multi-agent network, 54 experts working in parallel
- **Purple-cyan gradient**: WFC brand identity (AI intelligence + performance)

---

### 2. Championship Belt Compact (`logo-belt-compact.svg`)

**400x120px** - Compact belt for headers and navigation

**Use for:**

- Navigation bars
- Email signatures
- Compact headers
- Social media banners
- Terminal/CLI branding

---

## Classic Logo Variants (Legacy)

### 1. Full Logo (`logo-full.svg`)

**400x120px** - Complete branding with icon, wordmark, and tagline

**Use for:**

- Documentation headers
- Website hero sections
- Marketing materials
- GitHub social preview

**Light background version**

---

### 2. Full Logo Dark (`logo-full-dark.svg`)

**400x120px** - Optimized for dark backgrounds with lighter gradient

**Use for:**

- Dark mode websites
- Dark terminals/CLIs
- Video overlays
- Dark presentations

---

### 3. Wordmark (`logo-wordmark.svg`)

**300x80px** - "WFC" with tagline and accent bars

**Use for:**

- Navigation bars
- Email signatures
- Compact headers
- Social media banners

---

### 4. Icon Only (`logo-icon.svg`)

**100x100px** - Hexagonal network symbol representing multi-agent architecture

**Use for:**

- Profile pictures
- App icons
- Favicons (scaled)
- Social media avatars

**Design meaning:**

- Outer hexagon: Framework boundary
- 6 nodes: Panel of expert agents
- Center node: Consensus engine
- Connection lines: Parallel execution

---

### 5. Compact Icon (`logo-icon-compact.svg`)

**64x64px** - Minimal "W" on hexagonal badge

**Use for:**

- Favicon (16x16, 32x32, 64x64)
- Browser tabs
- Mobile app icons
- Notification icons

---

## Design System

### Colors

| Color | Hex | Usage |
|-------|-----|-------|
| **Purple** | `#7C3AED` | Primary (AI/Intelligence) |
| **Cyan** | `#06B6D4` | Secondary (Performance) |
| **Light Purple** | `#A78BFA` | Accent (Dark mode) |
| **Light Cyan** | `#22D3EE` | Accent (Dark mode) |
| **Gray** | `#64748B` | Text/Tagline |

### Typography

**Font:** Inter (system fallback: -apple-system, system-ui, sans-serif)

**Weights:**

- Wordmark "WFC": 900 (Black)
- Tagline: 600-700 (Semi-Bold/Bold)
- Subtext: 500 (Medium)

### Visual Metaphor

The hexagonal network represents:

- **54 expert personas** across 9 panels
- **Parallel execution** (independent agents)
- **Consensus synthesis** (center node)
- **Multi-perspective review** (multiple viewpoints converging)

---

## Usage Guidelines

### ✅ Do

- Use on light backgrounds (logo-full.svg)
- Use on dark backgrounds (logo-full-dark.svg)
- Maintain aspect ratio when scaling
- Ensure adequate padding around logo
- Use SVG format for crisp rendering

### ❌ Don't

- Modify colors or gradients
- Distort or stretch the logo
- Add effects or filters
- Use low-resolution raster formats
- Place on busy backgrounds

---

## Converting to PNG (if needed)

For raster formats, convert SVG at high resolution:

```bash
# Using ImageMagick
convert -density 300 logo-full.svg -resize 1200x logo-full.png

# Using Inkscape
inkscape logo-full.svg --export-png=logo-full.png --export-width=1200

# Using rsvg-convert
rsvg-convert -w 1200 logo-full.svg > logo-full.png
```

**Recommended PNG sizes:**

- Full logo: 1200x360px (3x scale)
- Icon: 512x512px
- Favicon: 64x64px, 32x32px, 16x16px

---

## Favicon Generation

```bash
# Generate favicon.ico with multiple sizes
convert logo-icon-compact.svg -define icon:auto-resize=64,32,16 favicon.ico
```

Or use online tools like [Real Favicon Generator](https://realfavicongenerator.net/)

---

## License

These logos are part of the WFC project and are licensed under MIT License.
Same terms as the main project - see [LICENSE](../LICENSE).

---

**This is World Fucking Class.** 🚀
