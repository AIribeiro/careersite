# Production assets

The public website now uses the original photography stored in the repository-level `/images` directory as its canonical media source.

`src/site_media.py` selects the most appropriate authentic photograph for each website context and embeds the original file bytes without recompression. The previous text-safe `site_photos_bundle/` mechanism is retired and should not be used for production photography.

Image selection is intentional: Home emphasizes executive presence; Leadership Impact emphasizes visible leadership in practice; Thinking emphasizes public thought leadership; About uses a more personal editorial portrait; Contact uses a direct executive portrait; and the role-lens pages use panel/dialogue imagery that supports their specific leadership context.

Historical source-image experiments remain outside the production path.
