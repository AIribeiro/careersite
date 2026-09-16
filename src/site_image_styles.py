IMAGE_CSS = """
<style>
/* Leadership photography is evidence: purposeful, responsive and never stretched beyond its useful display size. */
.hero .heroin{grid-template-columns:minmax(0,.88fr) minmax(500px,1.05fr);gap:34px;min-height:720px;padding:48px 0 54px}
.hero .portrait{overflow:hidden;background:#111b2c;width:100%;max-width:none;min-height:610px;align-self:stretch;justify-self:end;box-shadow:0 26px 70px rgba(0,0,0,.24)}
.hero .portrait img{width:100%;height:100%;min-height:610px;aspect-ratio:auto;object-fit:cover;object-position:52% 32%;display:block;image-rendering:auto}
.hero .portrait .note{left:22px;bottom:22px;width:min(350px,82%);box-shadow:0 18px 45px rgba(0,0,0,.28)}
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
@media(max-width:1100px){
  .hero .heroin{grid-template-columns:minmax(0,.92fr) minmax(430px,1fr);gap:28px}
  .hero .portrait{min-height:560px}
  .hero .portrait img{min-height:560px}
}
@media(max-width:980px){
  .hero .heroin{grid-template-columns:1fr;min-height:auto;padding:52px 0 58px}
  .hero .portrait{width:100%;max-width:820px;min-height:0;justify-self:start;align-self:auto}
  .hero .portrait img{height:auto;min-height:0;aspect-ratio:16/10;object-position:center 28%}
  .hero .portrait .note{left:18px;bottom:18px}
  .editorial-split,.contactvisual{grid-template-columns:1fr}
  .editorial-photo{justify-self:start}
  .contactportrait{justify-self:start;max-width:300px}
}
@media(max-width:620px){
  .hero .heroin{padding:42px 0 46px}
  .hero .portrait img,.speak img,.editorial-photo img,.lensphoto img{aspect-ratio:4/3}
  .hero .portrait .note{left:12px;bottom:12px;width:calc(100% - 24px)}
  .editorial-photo.portrait img{aspect-ratio:4/5}
  .contactportrait{max-width:260px}
}
</style>
"""
