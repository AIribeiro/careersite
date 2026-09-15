IMAGE_CSS = """
<style>
/* High-resolution leadership photography: sparse, purposeful, never decorative. */
.hero .portrait{overflow:hidden;background:#111b2c}
.hero .portrait img{width:100%;height:auto;aspect-ratio:4/3;object-fit:cover;object-position:center;display:block}
.speak img{width:100%;aspect-ratio:16/10;object-fit:cover;object-position:center;display:block}
@media(max-width:980px){
  .hero .portrait{max-width:820px}
  .hero .portrait img{aspect-ratio:16/10}
}
@media(max-width:620px){
  .hero .portrait img,.speak img{aspect-ratio:4/3}
}
</style>
"""
