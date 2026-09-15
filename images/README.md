# Website photography

The `/images` directory contains selected, web-optimized derivatives of Jair Ribeiro's original high-resolution photography. The original uploaded source files are not modified at runtime. Each public placement should reinforce a specific hiring signal rather than decorate the page.

Current visual roles:

- `jair-hero-executive.webp` — Home hero and selected contact/role-lens use. Close panel image emphasizing executive presence, communication and confidence.
- `jair-panel-dialogue.webp` — Home external credibility, Thinking and consulting lens. Shows dialogue, influence and contribution in an industry setting.
- `jair-ai-panel.webp` — Leadership Impact and enterprise lens. Reinforces business/technology dialogue and external AI credibility.
- `jair-thinking-panel.webp` — Thinking page. A quieter, reflective panel image that supports judgment, listening and point of view.
- `jair-about-bw.webp` — About page. Editorial black-and-white portrait used to humanize the professional arc without weakening executive positioning.

Image policy:

- Never upscale an image beyond its intrinsic pixel dimensions.
- Use CSS cropping (`object-fit: cover`) to adapt composition to desktop and mobile while preserving source resolution.
- Hero imagery loads eagerly; supporting photography loads lazily.
- `Media Quality` verifies that every selected source is decodable and meets the minimum dimensions required for its website placement.
- Runtime image failures must never crash the Streamlit application. `site_assets.py` verifies image bytes and retains a last-known-valid fallback for availability; quality enforcement belongs in CI.

The wider project contains additional photographs. They are intentionally not all displayed at once: curation is part of the executive visual system, and redundant or weaker images should remain source material rather than becoming a gallery.
