IMAGE_CSS = """
<style>
/* Leadership photography is evidence: purposeful, responsive and never stretched beyond its useful display size. */
.hero .portrait{overflow:hidden;background:#111b2c;width:min(100%,560px);justify-self:end}
.hero .portrait img{width:100%;height:auto;aspect-ratio:4/3;object-fit:cover;object-position:center 34%;display:block;image-rendering:auto}
.speak img{width:min(100%,700px);aspect-ratio:16/10;object-fit:cover;object-position:center;display:block;image-rendering:auto}
.editorial-split{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(280px,.85fr);gap:40px;align-items:center}
.editorial-photo{overflow:hidden;background:#111b2c;width:min(100%,520px);justify-self:end}
.editorial-photo img{display:block;width:100%;height:auto;aspect-ratio:4/3;object-fit:cover;object-position:center;image-rendering:auto}
.editorial-photo.portrait img{aspect-ratio:4/5;object-position:center 26%}
.contactvisual{display:grid;grid-template-columns:minmax(0,1fr) minmax(240px,320px);gap:48px;align-items:center}
.contactportrait{width:100%;max-width:320px;justify-self:end;overflow:hidden;background:#111b2c}
.contactportrait img{display:block;width:100%;height:auto;aspect-ratio:1/1;object-fit:cover;object-position:center 28%;image-rendering:auto}
.lensphoto{margin:24px 0;overflow:hidden;background:#111b2c;width:min(100%,640px)}
.lensphoto img{display:block;width:100%;height:auto;aspect-ratio:16/10;object-fit:cover;object-position:center;image-rendering:auto}
@media(max-width:980px){
  .hero .portrait{max-width:700px;justify-self:start}
  .hero .portrait img{aspect-ratio:16/10}
  .editorial-split,.contactvisual{grid-template-columns:1fr}
  .editorial-photo{justify-self:start}
  .contactportrait{justify-self:start;max-width:300px}
}
@media(max-width:620px){
  .hero .portrait img,.speak img,.editorial-photo img,.lensphoto img{aspect-ratio:4/3}
  .editorial-photo.portrait img{aspect-ratio:4/5}
  .contactportrait{max-width:260px}
}
</style>
"""
