"""Scoped visual system for the four executive pathways on Home only."""

from base64 import b64encode

from home_pathways import ICON_PATHS

HOME_PATHWAYS_CSS = """
<style>
/* Four matching editorial cards in warm paper and restrained copper. */
.site .journey-section.home-pathways{
  position:relative;isolation:isolate;overflow:hidden;
  padding:clamp(65px,7vw,95px) 0 clamp(72px,7.5vw,100px);
  background:
    radial-gradient(ellipse 75% 90% at 105% -20%,rgba(184,121,80,.12),transparent 72%),
    linear-gradient(145deg,#f7f3ed,#f1ece6);
  border-top:1px solid #dfd6cc;border-bottom:1px solid #ddd4ca;
}
.site .journey-section.home-pathways:before,.site .journey-section.home-pathways:after{
  content:"";z-index:-1;position:absolute;border-radius:50%;
  border:1px solid rgba(163,105,70,.12);pointer-events:none;
}
.site .journey-section.home-pathways:before{width:530px;height:530px;right:-180px;top:-190px}
.site .journey-section.home-pathways:after{width:360px;height:360px;right:-110px;top:-112px}
.site .journey-section.home-pathways .home-pathways-intro{
  display:grid;grid-template-columns:minmax(0,.94fr) minmax(0,1.06fr);
  gap:clamp(36px,6vw,85px);align-items:center;
  width:100%;max-width:none;margin:0 0 clamp(30px,4vw,48px);
}
.site .home-pathways-heading,.site .home-pathways-context{min-width:0}
.site .home-pathways-heading .eyebrow{
  color:#9c6443;font-size:11px;letter-spacing:.17em;margin:0 0 20px;
}
.site .home-pathways-heading h2{
  max-width:570px;margin:0;color:#1b2c3c;
  font:500 clamp(42px,5.1vw,64px)/1.04 Georgia,serif;
  letter-spacing:-.045em;text-wrap:balance;
}
.site .home-pathways-heading-rule{
  display:block;width:106px;height:3px;margin-top:29px;
  background:linear-gradient(90deg,#b17450 0 50%,rgba(177,116,80,.22) 50%);
}
.site .home-pathways-context>p{
  max-width:650px;margin:0;color:#4d5965;
  font-size:clamp(15px,1.35vw,17px);line-height:1.79;
}
.site .home-pathways-index{
  display:flex;flex-wrap:wrap;gap:12px 19px;align-items:center;
  margin-top:23px;padding-top:16px;
  border-top:1px solid rgba(49,58,65,.15);
  color:#7c6d62;font-size:11px;letter-spacing:.025em;
}
.site .home-pathways-index>span:first-child{
  color:#9b6747;font-size:10px;font-weight:850;
  text-transform:uppercase;letter-spacing:.12em;
}
.site .home-pathways-index>span+span:before{
  content:"";display:inline-block;width:4px;height:4px;
  margin:0 15px 2px 0;vertical-align:middle;
  background:#b17450;border-radius:50%;
}
.site .journey-section.home-pathways .home-pathways-grid{
  display:grid;grid-template-columns:repeat(2,minmax(0,1fr));
  gap:clamp(16px,2vw,22px);align-items:stretch;
}
.site .journey-section.home-pathways a.home-pathway-card{
  position:relative;isolation:isolate;overflow:hidden;
  display:flex;flex-direction:column;min-width:0;
  min-height:352px;height:100%;
  padding:clamp(27px,3vw,36px);
  border:1px solid #ddd4c9;border-radius:12px;
  background:linear-gradient(147deg,#fffefa,#faf7f2);
  box-shadow:0 17px 42px rgba(22,36,49,.045);
  color:#203244!important;text-decoration:none!important;
  transition:transform .22s ease,box-shadow .22s ease,border-color .22s ease;
}
.site .home-pathways a.home-pathway-card:before{
  content:"";position:absolute;top:0;left:0;width:140px;height:3px;
  background:linear-gradient(90deg,#a96944,#e2b08b);pointer-events:none;
}
.site .home-pathways a.home-pathway-card:after{
  content:"";position:absolute;z-index:-1;
  top:-100px;right:-75px;width:230px;height:230px;
  border:1px solid rgba(175,121,85,.14);
  border-radius:50%;pointer-events:none;
}
.site .journey-section.home-pathways a.home-pathway-card:hover{
  transform:translateY(-4px);border-color:#bf967b;
  box-shadow:0 27px 56px rgba(25,39,52,.135);
}
.site .journey-section.home-pathways a.home-pathway-card:focus-visible{
  outline:3px solid #a76842;outline-offset:4px;
}
.site .home-pathway-top{
  display:flex;justify-content:space-between;align-items:flex-start;
  gap:22px;width:100%;margin-bottom:29px;
}
.site .home-pathway-icon{
  display:inline-flex;flex:0 0 62px;align-items:center;justify-content:center;
  width:62px;height:62px;border:1px solid #e4d4c6;border-radius:13px;
  color:#a16947;background:linear-gradient(145deg,#fcf3e9,#f1e5d8);
}
.site .home-pathway-number{
  color:#c6b6a7;font:500 35px/1 Georgia,serif;letter-spacing:-.045em;
}
.site .home-pathway-body{display:block;flex:1 1 auto}
.site .journey-section.home-pathways .home-pathway-body .journey-step{
  display:block;min-height:0;margin:0 0 12px;
  color:#a16947;font-size:10px;font-weight:850;
  text-transform:uppercase;letter-spacing:.15em;line-height:1.45;
}
.site .journey-section.home-pathways .home-pathway-body h3{
  min-height:0;margin:0 0 16px;color:#1d3040;
  font:500 clamp(31px,3.3vw,41px)/1.11 Georgia,serif;
  letter-spacing:-.025em;
}
.site .journey-section.home-pathways .home-pathway-body p{
  max-width:480px;margin:0;color:#596675;
  font-size:15px;line-height:1.72;
}
.site .home-pathway-footer{
  display:flex;flex-wrap:wrap;justify-content:space-between;align-items:end;
  gap:12px 20px;width:100%;
  margin-top:32px;padding-top:21px;border-top:1px solid #e7ddd3;
}
.site .home-pathway-context{
  color:#917d6f;font-size:10px;font-weight:750;letter-spacing:.04em;
}
.site .home-pathway-cta{
  display:inline-flex;align-items:center;gap:12px;margin-left:auto;
  color:#263b4d;font-size:13px;font-weight:800;line-height:1.45;
}
.site .home-pathway-arrow{
  display:inline-flex;flex:0 0 32px;align-items:center;justify-content:center;
  width:32px;height:32px;border-radius:50%;border:1px solid #e3d4c7;
  color:#a46b49;font-size:19px;font-weight:400;
  transition:transform .2s ease,background .2s ease;
}
.site .home-pathways a.home-pathway-card:hover .home-pathway-arrow{
  transform:translate(2px,-2px);background:#f3e7db;
}
@media(max-width:1000px){
  .site .journey-section.home-pathways .home-pathways-intro{
    grid-template-columns:minmax(0,1fr);gap:22px;
  }
  .site .home-pathways-heading h2{max-width:770px}
  .site .home-pathways-heading-rule{margin-top:22px}
  .site .journey-section.home-pathways a.home-pathway-card{min-height:332px}
}
@media(max-width:720px){
  .site .journey-section.home-pathways{padding:56px 0 65px}
  .site .journey-section.home-pathways .home-pathways-grid{
    grid-template-columns:minmax(0,1fr);gap:14px;
  }
  .site .journey-section.home-pathways a.home-pathway-card{
    min-height:0;padding:27px 25px 26px;border-radius:10px;
  }
  .site .home-pathway-top{margin-bottom:23px}
  .site .home-pathway-icon{width:54px;height:54px;flex-basis:54px}
  .site .journey-section.home-pathways .home-pathway-body h3{
    margin-bottom:12px;font-size:clamp(30px,7.8vw,38px);
  }
  .site .home-pathway-footer{margin-top:25px}
  .site .home-pathways-index>span+span:before{display:none}
}
@media(max-width:440px){
  .site .home-pathways-heading h2{font-size:clamp(39px,10vw,48px)}
  .site .home-pathway-footer{align-items:flex-start;flex-direction:column}
  .site .home-pathway-cta{margin-left:0}
}
@media(prefers-reduced-motion:reduce){
  .site .journey-section.home-pathways a.home-pathway-card,
  .site .home-pathway-arrow{transition:none}
  .site .journey-section.home-pathways a.home-pathway-card:hover,
  .site .home-pathways a.home-pathway-card:hover .home-pathway-arrow{
    transform:none;
  }
}
</style>
"""

def _icon_css() -> str:
    """Embed vector icons in CSS since Streamlit sanitizes inline SVG markup.

    Data URIs work in Safari without network requests or external icon fonts.
    """
    rules = []
    for name, paths in ICON_PATHS.items():
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" '
            'viewBox="0 0 32 32" fill="none" stroke="#a16947" '
            'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">'
            + paths + '</svg>'
        )
        payload = b64encode(svg.encode("utf-8")).decode("ascii")
        rules.append(
            f'.site .home-pathways .home-pathway-card--{name} .home-pathway-icon'
            '{background-image:'
            f'url("data:image/svg+xml;base64,{payload}"),'
            'linear-gradient(145deg,#fcf3e9,#f1e5d8);'
            'background-repeat:no-repeat;'
            'background-size:32px 32px,cover;'
            'background-position:center,center;}'
        )
    return "\n".join(rules)


HOME_PATHWAYS_CSS = HOME_PATHWAYS_CSS.replace(
    "</style>",
    _icon_css() + "\n</style>",
)
