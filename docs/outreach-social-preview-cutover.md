# Outreach social preview cutover

The masked Spaceship forwarder cannot expose the portfolio's Open Graph head to LinkedIn. The existing static Pages bridge serves metadata and a real 1200×630 PNG; the dedicated outreach endpoint also defaults to source=outreach if the forwarder drops query parameters.

## Safe cutover

1. Verify the Pages deployment at https://airibeiro.github.io/careersite/outreach/ and the image at https://airibeiro.github.io/careersite/social/jair-ribeiro-home.png.
2. In Spaceship Domain List > jairribeiro.com > URL Redirects, inspect the existing go host entry. If it is used for outreach only, replace masked forwarding with an unmasked 301 to https://airibeiro.github.io/careersite/outreach/. If go is used by other routes too, verify that forwarding preserves path/query before changing; do not cut over if it drops article/page attribution. A separate outreach-only host or a proper server-rendered edge front door may be required.
3. Leave root, other subdomains, mail and authentication DNS untouched. The outreach bridge sends browsers to https://jairribeiro.com/?source=outreach and preserves the existing public route and campaign allowlist when supplied. It intentionally does not relay private authentication tokens.
4. Fetch the exact original URL with LinkedInBot and ordinary browser user agents. Confirm the final response exposes og:title, og:description, og:image and og:url, the image is accessible, and the browser opens the original portfolio with source=outreach. Verify other active go links still reach their intended destination.
5. Refresh the exact URL in https://www.linkedin.com/post-inspector/ and inspect the card. Do not mark complete until live verification succeeds.
6. Rollback: restore the recorded previous go forwarding entry if any route breaks. A 301 may be cached; avoid changing other hosts.

This repository change does not alter registrar configuration. The generic bridge is not an article-specific preview; individual articles retain their established dedicated share pages.
