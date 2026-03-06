---
description: Generate a beautiful standalone HTML diagram and open it in the browser
skill: wfc-visual
---
Generate an HTML diagram for: $@

Follow the wfc-visual skill workflow. Read the reference template and CSS patterns before generating. Pick a distinctive aesthetic that fits the content — vary fonts, palette, and layout style from previous diagrams.

Consult `./references/design-intelligence.md` to select an industry-appropriate palette and font pairing if the content has a clear domain.

If `surf` CLI is available (`which surf`), consider generating an AI illustration via `surf gemini --generate-image` when an image would genuinely enhance the page — a hero banner, conceptual illustration, or educational diagram that Mermaid can't express. Match the image style to the page's palette. Embed as base64 data URI. See css-patterns.md "Generated Images" for container styles. Skip images when the topic is purely structural or data-driven.

Write to `~/.agent/diagrams/` and open the result in the browser.
