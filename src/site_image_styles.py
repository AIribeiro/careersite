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
/* About / Professional arc: integrate the portrait into the reading flow, not a second column. */
.about-professional-arc{display:flow-root}
.about-professional-arc .about-arc-photo{
  float:right;
  width:clamp(205px,27%,320px);
  max-width:100%;
  margin:5px 0 18px clamp(22px,3vw,38px);
  overflow:hidden;
  background:#111b2c;
}
.about-professional-arc .about-arc-photo img{
  display:block;
  width:100%;
  height:auto;
  aspect-ratio:4/5;
  object-fit:cover;
  object-position:center 26%;
  image-rendering:auto;
}
@media(max-width:600px){
  .about-professional-arc .about-arc-photo{
    float:none;
    width:min(100%,300px);
    margin:17px auto 22px;
  }
}
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

/* Contact page closing: warm, editorial two-column finish.
   Keep the original panel photograph; no generated portrait or fixed-height
   spacer. Maintain the split on iPad and collapse only on narrow phones. */
.site .contact-closing{
  position:relative;
  isolation:isolate;
  overflow:hidden;
  padding:clamp(52px,6vw,82px) 0;
  background:radial-gradient(ellipse at 91% 18%,rgba(233,177,150,.16),transparent 34%),
             linear-gradient(115deg,#fdfaf6 0%,#faf5f0 100%);
}
.site .contact-closing::before{
  content:"";
  pointer-events:none;
  position:absolute;
  width:min(850px,70vw);
  height:min(850px,70vw);
  right:-35%;
  bottom:-115%;
  border:1px solid rgba(195,117,77,.13);
  border-radius:50%;
}
.site .contact-closing .contactvisual{
  position:relative;
  z-index:1;
  display:grid;
  grid-template-columns:minmax(0,1.06fr) minmax(0,.94fr);
  gap:clamp(24px,4.8vw,65px);
  align-items:center;
}
.site .contact-closing .contact-closing-copy{min-width:0;max-width:610px}
.site .contact-closing .contact-closing-eyebrow{
  display:flex;
  gap:20px;
  align-items:center;
  margin:0 0 clamp(26px,3vw,39px);
  color:#a3573d;
  font-size:11px;
  font-weight:800;
  letter-spacing:.21em;
}
.site .contact-closing .contact-closing-eyebrow::after{
  content:"";
  flex:0 0 48px;
  height:1px;
  background:#c98363;
}
.site .contact-closing h2{
  max-width:690px;
  margin:0;
  color:#1c2535;
  font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;
  font-weight:720;
  font-size:clamp(36px,4.45vw,61px);
  line-height:1.11;
  letter-spacing:-.035em;
  text-wrap:balance;
}
.site .contact-closing .contact-closing-copy>p:not(.eyebrow){
  max-width:590px;
  margin:clamp(24px,3vw,38px) 0 0;
  color:#4b5361;
  font-size:clamp(15px,1.42vw,18px);
  line-height:1.72;
}
.site .contact-closing .contact-closing-rule{
  display:block;
  margin-top:clamp(28px,5vw,61px);
  width:min(75%,350px);
  border-top:1px solid #dcd2ca;
}
.site .contact-closing .contact-closing-visual{
  position:relative;
  width:100%;
  max-width:475px;
  min-width:0;
  justify-self:end;
  padding:0 12px 0 0;
}
.site .contact-closing .contact-closing-visual::before{
  content:"";
  position:absolute;
  top:-19px;
  right:-8px;
  width:60%;
  height:52%;
  border-radius:22px;
  background:linear-gradient(145deg,rgba(250,222,210,.94),rgba(244,204,187,.82));
}
.site .contact-closing .contactportrait{
  position:relative;
  z-index:1;
  width:100%;
  max-width:none;
  margin:0;
  overflow:hidden;
  border-radius:15px;
  background:#1a2133;
  border:1px solid rgba(55,44,48,.12);
  box-shadow:0 24px 52px rgba(32,30,35,.16);
}
.site .contact-closing .contactportrait img{
  display:block;
  width:100%;
  height:auto;
  aspect-ratio:4/5;
  object-fit:cover;
  object-position:53% 45%;
  image-rendering:auto;
}
@media(max-width:850px){
  .site .contact-closing{padding:48px 0 54px}
  .site .contact-closing .contactvisual{grid-template-columns:minmax(0,1.1fr) minmax(0,.9fr);gap:25px}
  .site .contact-closing h2{font-size:clamp(32px,4.55vw,40px)}
  .site .contact-closing .contact-closing-copy>p:not(.eyebrow){font-size:14px;line-height:1.62}
  .site .contact-closing .contact-closing-eyebrow{font-size:10px;margin-bottom:23px}
  .site .contact-closing .contact-closing-rule{margin-top:25px}
}
@media(max-width:700px){
  .site .contact-closing{padding:47px 0 53px}
  .site .contact-closing .contactvisual{grid-template-columns:minmax(0,1fr);gap:37px}
  .site .contact-closing .contact-closing-copy{max-width:560px}
  .site .contact-closing h2{font-size:clamp(35px,8vw,45px)}
  .site .contact-closing .contact-closing-copy>p:not(.eyebrow){font-size:15px;line-height:1.68}
  .site .contact-closing .contact-closing-rule{margin-top:25px}
  .site .contact-closing .contact-closing-visual{max-width:580px;justify-self:start}
  .site .contact-closing .contactportrait img{aspect-ratio:5/4;object-position:53% 44%}
}
@media(prefers-reduced-motion:reduce){
  .site .contact-closing *{scroll-behavior:auto}
}
</style>
"""
