# Website photography

This directory contains the curated production photography used by the public site.

`site_photos_bundle/` is the single canonical media bundle. It contains five selected, web-optimized leadership images used for the Home, Leadership Impact, Thinking, About and role-lens views. The bundle is stored as text-safe chunks so Streamlit deployment remains portable and does not depend on an external media host.

The wider historical source-image experiments are intentionally not kept on the default branch. The pre-cleanup repository state is preserved on `archive/pre-public-cleanup-2026-09-16`.

Image policy:

- use authentic photography only;
- preserve source aspect and use CSS cropping for placement;
- avoid decorative galleries and redundant images;
- validate the canonical bundle in CI;
- never use stock or futuristic AI imagery as a substitute for professional evidence.
