"""A responsive, source-grounded featured AI & Data Governance infographic."""

GOVERNANCE_FEATURE = r'''
<style>
.site .gf{isolation:isolate;position:relative;background:radial-gradient(ellipse at 5% 6%,#104764 0%,transparent 32%),linear-gradient(130deg,#051525,#092b45);color:#eefaff;padding:clamp(64px,7vw,112px) 0;content-visibility:auto;contain-intrinsic-size:auto 1850px}
.site .gf *{box-sizing:border-box}
.site .gf .gw{width:min(1480px,calc(100% - 44px));margin:auto}
.site .gf .intro{display:flex;gap:50px;align-items:end;justify-content:space-between;margin-bottom:34px}
.site .gf .ey{font:800 11px Inter,sans-serif;letter-spacing:.18em;color:#6ae4fc;text-transform:uppercase;margin:0}
.site .gf h2{color:#fff;font:750 clamp(40px,5.5vw,76px)/1.03 Inter,sans-serif;letter-spacing:-.055em;margin:17px 0 0}
.site .gf h2 em{font-style:normal;color:#69dff6}
.site .gf .deck{color:#b5d4e3;font:450 clamp(15px,1.45vw,19px)/1.6 Inter,sans-serif;max-width:390px;margin:0}
.site .gf .infographic{margin:0;border:1px solid #397999;border-radius:24px;background:linear-gradient(130deg,#09283d,#061b30 60%,#0a3249);padding:clamp(20px,3vw,47px);box-shadow:0 32px 85px rgba(0,0,0,.27)}
.site .gf .meta{display:flex;justify-content:space-between;gap:12px;color:#75dcef;font:800 10px Inter,sans-serif;letter-spacing:.17em;text-transform:uppercase;margin:0 0 23px}
.site .gf .two{display:grid;grid-template-columns:1fr 1fr;gap:15px}
.site .gf .foundation{background:rgba(17,112,153,.18);border:1px solid #326b88;border-radius:16px;padding:24px;min-width:0}
.site .gf .foundation h3{font:750 23px Inter,sans-serif;color:white;margin:0 0 12px}
.site .gf .foundation p{font:480 14px/1.7 Inter,sans-serif;color:#b9d7e6;margin:0}
.site .gf .foundation h3:before{content:"";display:inline-block;width:14px;height:14px;border:2px solid #73ebff;border-radius:4px;margin-right:12px}
.site .gf .converge{display:flex;align-items:center;gap:16px;text-align:center;justify-content:center;margin:25px 0 14px;font:800 12px Inter,sans-serif;letter-spacing:.1em;color:#63dff7;text-transform:uppercase}
.site .gf .converge:before,.site .gf .converge:after{content:"";height:1px;flex:1;max-width:200px;background:#225b7a}
.site .gf .account{border-radius:11px;border:1px solid #2f7a99;background:#0c3c59;color:#d7f3fa;padding:16px;text-align:center;font:650 15px/1.55 Inter,sans-serif}
.site .gf .account b{color:#6eebff}
.site .gf .label{font:800 11px/1.5 Inter,sans-serif;letter-spacing:.13em;text-transform:uppercase;color:#69e4f9;margin:0 0 15px}
.site .gf .operating{display:grid;grid-template-columns:minmax(190px,.95fr) minmax(420px,1.9fr) minmax(205px,1fr);gap:15px;margin-top:27px}
.site .gf .panel{border:1px solid #2a5672;border-radius:16px;background:rgba(4,28,48,.6);padding:21px 19px;min-width:0}
.site .gf ul,.site .gf ol{padding:0;margin:0;list-style:none}
.site .gf .panel li{padding:10px 0;border-bottom:1px solid #204560}
.site .gf .panel li:last-child{border:0}
.site .gf .panel li strong{display:block;color:#eefbff;font:750 14px/1.3 Inter,sans-serif}
.site .gf .panel li span{display:block;margin-top:6px;color:#a7c4d3;font:450 12px/1.5 Inter,sans-serif}
.site .gf .principles li strong{color:#b7eeff}
.site .gf .cycle{padding:23px 8px 15px;text-align:center;background:radial-gradient(circle at 50% 48%,rgba(12,111,144,.24),transparent 66%),#061f35}
.site .gf .cycle p.sub{color:#9dbfd0;font:450 12px/1.5 Inter,sans-serif;margin:0}
.site .gf .stage{position:relative;width:100%;max-width:590px;aspect-ratio:1;margin:0 auto}
.site .gf .ring{position:absolute;inset:5%;width:90%;height:90%;overflow:visible}
.site .gf .ring circle{fill:none;stroke:#2389ad;stroke-width:2;stroke-dasharray:5 8}
.site .gf .ring path{fill:none;stroke:#39d4ee;stroke-width:4;stroke-linecap:round}
.site .gf .node{position:absolute;left:var(--x);top:var(--y);transform:translate(-50%,-50%);width:31%;min-height:82px;background:linear-gradient(145deg,#e8fbff,#b8dfef);color:#0b354c;border-radius:13px;border:1px solid #80d9ef;padding:10px 8px;box-shadow:0 10px 20px #0003}
.site .gf .node b{font:800 14px Inter,sans-serif}
.site .gf .node small{font:900 11px Inter,sans-serif;color:#12748f;margin-right:7px}
.site .gf .node span{display:block;font:500 11px/1.35 Inter,sans-serif;margin-top:5px}
.site .gf .core{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:41%;aspect-ratio:1;border-radius:50%;border:2px solid #50e7fa;background:#092c43;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:12px;box-shadow:0 0 38px #00c8f326}
.site .gf .core small{font:850 10px Inter,sans-serif;letter-spacing:.1em;color:#78ecfd}
.site .gf .core strong{color:#fff;font:850 clamp(18px,1.65vw,25px)/1.06 Inter,sans-serif;margin:8px 0}
.site .gf .core span{font:550 12px/1.4 Inter,sans-serif;color:#b9e6f0}
.site .gf .cycle .footnote{font:550 11px/1.6 Inter,sans-serif;color:#8eafc4;margin:0 14px}
.site .gf .bottom{display:grid;grid-template-columns:1fr 1.14fr .9fr;gap:15px;margin-top:15px}
.site .gf .bottom .panel li{border:1px solid #29516b;border-radius:8px;background:#11354a;padding:9px 11px;margin-bottom:7px}
.site .gf .bottom .panel li:last-child{margin-bottom:0;border:1px solid #29516b}
.site .gf .bottom .panel li strong{font-size:12px;color:#e8faff}
.site .gf .bottom .panel li span{margin-top:2px;font-size:11px}
.site .gf .bottom .approval li{display:flex;align-items:start;gap:10px}
.site .gf .approval i{font:900 11px Inter,sans-serif;font-style:normal;flex:0 0 23px;height:23px;border-radius:50%;background:#aee8f4;color:#0b3449;display:grid;place-items:center}
.site .gf .response li{border-left:3px solid #6de3f2!important}
.site .gf .response li:last-child{border-left-color:#dbab7a!important}
.site .gf .signals{border:1px solid #46adcb;border-radius:16px;background:#0b354e;margin-top:15px;padding:25px 14px}
.site .gf .signals h3{font:750 13px Inter,sans-serif;letter-spacing:.11em;text-align:center;margin:0 0 23px;color:#d5f6fc}
.site .gf .four{display:grid;grid-template-columns:repeat(4,minmax(0,1fr))}
.site .gf .four div{text-align:center;border-right:1px solid #37728c;padding:0 12px}
.site .gf .four div:last-child{border:0}
.site .gf .four strong{font:850 clamp(20px,2.2vw,30px) Inter,sans-serif;color:#68eafd}
.site .gf .four span{display:block;color:#c2dce8;font:480 12px/1.5 Inter,sans-serif;margin-top:10px}
.site .gf .takeaway{background:linear-gradient(90deg,#c8f3fc,#80e0f4,#c4f2fd);color:#082b40;border-radius:12px;padding:19px 22px;margin:15px 0 0;text-align:center;font:750 clamp(17px,1.65vw,23px)/1.4 Inter,sans-serif}
.site .gf figcaption{display:flex;align-items:center;justify-content:space-between;border-top:1px solid #2a5972;margin-top:24px;padding-top:18px;gap:15px}
.site .gf figcaption strong{font:750 20px Inter,sans-serif;color:#fff}
.site .gf figcaption small{display:block;margin-top:5px;color:#9fc5d4;font:500 12px Inter,sans-serif}
.site .gf figcaption .badge{border-radius:20px;border:1px solid #398fa7;padding:8px 14px;color:#76e3f7;font:800 10px Inter,sans-serif;letter-spacing:.13em}
.site .gf .after{display:flex;align-items:center;justify-content:space-between;gap:20px;margin-top:27px}
.site .gf .after p{max-width:900px;font:480 15px/1.7 Inter,sans-serif;color:#b9d0dd;margin:0}
.site .gf .after a{border:1px solid #3b829b;padding:13px 16px;color:#c7effa;text-decoration:none;font:700 12px Inter,sans-serif;white-space:nowrap}
.site .gf .after a:hover{background:#124b63}

/* Premium framework refinement: calm contrast, precise rhythm, a dominant decision hub. */
.site .gf{background:radial-gradient(ellipse at 8% 0%,rgba(20,78,105,.56),transparent 39%),linear-gradient(135deg,#051727,#071d30 58%,#0a293d)}
.site .gf .infographic{background:linear-gradient(145deg,#082337,#071d30 56%,#092b42);border-color:#3a7189;box-shadow:0 25px 68px rgba(0,5,14,.28)}
.site .gf .intro{gap:clamp(28px,4vw,58px)}
.site .gf .foundation{padding:clamp(20px,2.1vw,29px);border-color:#345f76;background:rgba(17,76,104,.32)}
.site .gf .foundation-head{display:flex;align-items:center;gap:17px;margin-bottom:13px}
.site .gf .foundation-symbol{width:47px;height:47px;flex:0 0 47px;display:grid;place-items:center;border-radius:14px;border:1px solid rgba(96,207,234,.36);background:rgba(6,171,211,.09);color:#64e1f5}
.site .gf .foundation-symbol svg{width:29px;height:29px;fill:none;stroke:currentColor;stroke-width:1.65;stroke-linecap:round;stroke-linejoin:round}
.site .gf .foundation h3{font-size:clamp(20px,1.6vw,25px);margin:0}
.site .gf .foundation h3:before{content:none}
.site .gf .foundation p{font-size:clamp(13px,1.01vw,15px);line-height:1.75}
.site .gf .converge{margin:28px 0 17px;color:#83d6e6;font-size:12px}
.site .gf .account{padding:19px 22px;border-color:#3a8097;background:#103b53;font-size:clamp(13px,1.07vw,16px)}
.site .gf .operating{grid-template-columns:minmax(205px,1fr) minmax(460px,2.25fr) minmax(220px,1.05fr);gap:17px;margin-top:29px}
.site .gf .panel{border-color:#345f76;border-radius:17px;background:rgba(5,32,52,.77);padding:clamp(19px,1.5vw,24px)}
.site .gf .label{font-size:12px;letter-spacing:.11em;line-height:1.4;min-height:35px;margin-bottom:15px;color:#76ddec}
.site .gf .panel li{padding:13px 0;border-color:rgba(112,184,211,.16)}
.site .gf .panel li strong{font-size:clamp(13px,1vw,15px);line-height:1.33;letter-spacing:-.005em}
.site .gf .panel li span{font-size:clamp(11.5px,.87vw,13.5px);line-height:1.55;color:#aec8d7}
.site .gf .principles{display:flex;flex-direction:column}
.site .gf .principles .principle-note{margin:auto 0 0;padding:25px 0 0;border-top:1px solid rgba(111,183,211,.2);color:#79c7da;font:600 12.5px/1.7 Inter,sans-serif}
.site .gf .cycle{background:radial-gradient(circle at 50% 47%,rgba(10,84,113,.23),transparent 62%),#061f33;border-color:#3b89a2;padding:26px 9px 20px}
.site .gf .cycle .label{margin-bottom:2px}
.site .gf .stage{max-width:630px;margin:14px auto 17px}
.site .gf .ring circle{opacity:.64;stroke-width:1.35}
.site .gf .ring path{stroke-width:3.2;opacity:.76}
.site .gf .node{width:29%;min-height:89px;background:linear-gradient(148deg,#d7f0f6,#a7d1e1);border-color:#8ccee0;border-radius:13px;box-shadow:0 7px 18px rgba(0,4,11,.14)}
.site .gf .node b{font-size:clamp(13px,1vw,16px)}
.site .gf .node span{font-size:clamp(10.5px,.82vw,12px);line-height:1.45}
.site .gf .core{width:44%;border-color:#68e2ef;background:#092c43;box-shadow:0 0 0 7px rgba(64,195,220,.055)}
.site .gf .core strong{font-size:clamp(20px,1.7vw,27px);letter-spacing:-.045em;line-height:1.1}
.site .gf .core span{font-size:clamp(11px,.92vw,14px)}
.site .gf .cycle .footnote{font-size:12px;line-height:1.6;color:#a5c6d5}
.site .gf .bottom{grid-template-columns:1.05fr 1.15fr .97fr;gap:17px;margin-top:17px}
.site .gf .bottom .panel{padding:23px 19px}
.site .gf .bottom .panel li{background:rgba(20,65,88,.45);border:1px solid rgba(81,139,167,.32);padding:12px 12px;border-radius:9px;margin-bottom:9px}
.site .gf .bottom .panel li:last-child{border:1px solid rgba(81,139,167,.32)}
.site .gf .bottom .panel li strong{font-size:13px;color:#f2fbff}
.site .gf .bottom .panel li span{font-size:12px;line-height:1.52;color:#bed8e4}
.site .gf .approval i{background:#9bdce9;color:#092b42}
.site .gf .response{display:flex;flex-direction:column}
.site .gf .response ol{flex:1;display:flex;flex-direction:column;justify-content:space-between;gap:9px}
.site .gf .response li{position:relative;flex:1;display:flex;flex-direction:column;justify-content:center;min-height:76px}
.site .gf .response li:not(:last-child):after{content:"↓";position:absolute;bottom:-14px;left:50%;transform:translateX(-50%);color:#69ddec;z-index:2;font:800 15px Inter,sans-serif}
.site .gf .signals{margin-top:19px;padding:30px 20px;border-color:#3a8fa6;background:rgba(14,57,78,.75)}
.site .gf .signals h3{margin-bottom:25px}
.site .gf .four div{padding:0 18px}
.site .gf .four strong{color:#80dff0}
.site .gf .four span{font-size:clamp(12px,1.02vw,15px);line-height:1.55}
.site .gf .takeaway{margin-top:17px;border:1px solid rgba(87,209,230,.42);border-left:4px solid #70e5f4;border-radius:11px;background:linear-gradient(90deg,#10445c,#0c354e);color:#e7f8fc;font-size:clamp(17px,1.55vw,23px);padding:21px 24px;box-shadow:none}
.site .gf figcaption{margin-top:27px}
@media(max-width:1160px){
.site .gf .operating{grid-template-columns:1fr 1fr}
.site .gf .stage{max-width:630px}
.site .gf .bottom{grid-template-columns:1fr 1fr}
.site .gf .response{grid-column:1/-1}
.site .gf .response ol{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}
.site .gf .response li{min-height:100px;margin-bottom:0}
.site .gf .response li:not(:last-child):after{content:"→";left:auto;bottom:auto;right:-15px;top:40%;transform:none}
.site .gf .principles .principle-note{padding-top:16px;margin-top:15px}
}
@media(max-width:740px){
.site .gf .operating,.site .gf .bottom{grid-template-columns:1fr}
.site .gf .response{grid-column:auto}
.site .gf .response ol{grid-template-columns:1fr}
.site .gf .response li{min-height:77px}
.site .gf .response li:not(:last-child):after{content:"↓";left:50%;right:auto;bottom:-15px;top:auto;transform:translateX(-50%)}
.site .gf .foundation-head{gap:12px}
.site .gf .foundation-symbol{width:41px;height:41px;flex-basis:41px}
.site .gf .foundation-symbol svg{width:25px;height:25px}
.site .gf .foundation h3{font-size:20px}
.site .gf .label{min-height:0}
.site .gf .principles .principle-note{margin-top:19px}
.site .gf .signals{padding:22px 15px}
.site .gf .four div{padding:0 11px}
}
@media(max-width:480px){
.site .gf .stage{margin:17px auto 10px}
.site .gf .node{min-height:98px;width:auto}
.site .gf .node span{font-size:12px}
.site .gf .core{height:111px;width:100%}
.site .gf .meta{flex-wrap:wrap;gap:7px;line-height:1.6}
.site .gf .account{padding:15px 12px;line-height:1.65}
.site .gf .takeaway{padding:18px 15px}
}
@media(max-width:1160px){
.site .gf .operating{grid-template-columns:1fr 1fr}
.site .gf .cycle{grid-column:1/-1;grid-row:1}
.site .gf .bottom{grid-template-columns:1fr 1fr}
.site .gf .bottom .response{grid-column:1/-1}
.site .gf .stage{max-width:630px}
}
@media(max-width:740px){
.site .gf{padding:54px 0}.site .gf .gw{width:calc(100% - 28px)}
.site .gf .intro{display:block}.site .gf .deck{margin:17px 0 0}
.site .gf .infographic{padding:17px;border-radius:15px}
.site .gf .two,.site .gf .operating,.site .gf .bottom{grid-template-columns:1fr}
.site .gf .cycle{grid-column:auto;grid-row:1}
.site .gf .bottom .response{grid-column:auto}
.site .gf .foundation{padding:18px}
.site .gf .meta{font-size:9px}.site .gf .after{display:block}
.site .gf .after a{display:block;text-align:center;white-space:normal;margin-top:20px}
.site .gf .four{grid-template-columns:1fr 1fr;row-gap:22px}
.site .gf .four div:nth-child(2){border:0}
}
@media(max-width:480px){
.site .gf .ring{display:none}
.site .gf .stage{aspect-ratio:auto;display:grid;grid-template-columns:1fr 1fr;gap:8px;padding-top:115px}
.site .gf .node{position:static;transform:none;width:auto;min-height:98px}
.site .gf .core{left:0;top:0;transform:none;width:100%;height:111px;aspect-ratio:auto;border-radius:13px}
.site .gf .core strong{font-size:19px}.site .gf .core span{font-size:11px}
.site .gf .cycle .footnote{margin-top:12px}
.site .gf figcaption strong{font-size:17px}.site .gf figcaption small{font-size:10px}
}

/* Executive iconography: consistent 1.65px line weight, restrained tint and semantic placement. */
.site .gf .gf-icon{display:inline-grid;place-items:center;flex:none;margin:0;color:#77dce9;border:1px solid rgba(114,208,228,.26);background:rgba(77,171,203,.09);border-radius:11px}
.site .gf .gf-icon svg{display:block;width:23px;height:23px;overflow:visible}
.site .gf .gf-icon-row{display:flex;align-items:flex-start;gap:13px;min-width:0}
.site .gf .gf-icon-copy{min-width:0;flex:1}
.site .gf .panel li .gf-icon-principle{width:39px;height:39px;margin:1px 0 0}
.site .gf .panel li .gf-icon-principle svg{width:23px;height:23px}
.site .gf .principles li{padding:15px 0}
.site .gf .bottom .panel li.gf-mechanism{display:flex;align-items:flex-start;gap:12px;padding:13px}
.site .gf .bottom .panel li.gf-mechanism .gf-icon-mechanism{width:38px;height:38px;margin:0;border-radius:10px}
.site .gf .bottom .panel li.gf-mechanism .gf-icon-mechanism svg{width:22px;height:22px}
.site .gf .bottom .panel li.gf-mechanism .gf-icon-copy{padding-top:1px}
.site .gf .four .gf-signal{display:flex;flex-direction:column;align-items:center;justify-content:flex-start}
.site .gf .four .gf-icon-signal{width:48px;height:48px;margin:0 auto 15px;border:1px solid rgba(112,215,237,.24);background:rgba(76,161,186,.12);border-radius:15px}
.site .gf .four .gf-icon-signal svg{width:27px;height:27px}
.site .gf .core .gf-icon-core{width:42px;height:42px;margin:0 auto;border:0;background:transparent;color:#85e7ee}
.site .gf .core .gf-icon-core svg{width:34px;height:34px}
.site .gf .core{gap:4px}
.site .gf .core strong{margin:3px 0}
@media(max-width:740px){
.site .gf .panel li .gf-icon-principle{width:39px;height:39px}
.site .gf .bottom .panel li.gf-mechanism .gf-icon-mechanism{width:39px;height:39px}
.site .gf .four .gf-icon-signal{width:45px;height:45px;margin-bottom:11px}
}
@media(max-width:480px){
.site .gf .stage{padding-top:139px}
.site .gf .core{height:132px;gap:2px}
.site .gf .core .gf-icon-core{width:28px;height:28px}
.site .gf .core .gf-icon-core svg{width:24px;height:24px}
.site .gf .core strong{font-size:18px;line-height:1.07;margin:2px 0}
.site .gf .core span{font-size:10px;line-height:1.25}
.site .gf .four .gf-icon-signal{width:43px;height:43px}
.site .gf .four .gf-icon-signal svg{width:24px;height:24px}
}

/* Sanitizer-safe visual assets: no inline SVG DOM. CSS-hosted SVGs render as self-contained paint, no network requests. */
.site .gf .gf-icon::before{content:"";display:block;width:23px;height:23px;background-size:contain;background-repeat:no-repeat;background-position:center;flex:none}
.site .gf .foundation-symbol::before{content:"";display:block;width:29px;height:29px;background-size:contain;background-repeat:no-repeat;background-position:center}
.site .gf .gf-icon-signal::before{width:27px;height:27px}
.site .gf .gf-icon-core::before{width:34px;height:34px}
@media(max-width:480px){.site .gf .gf-icon-core::before{width:24px;height:24px}.site .gf .gf-icon-signal::before{width:24px;height:24px}}
.site .gf .foundation:nth-child(1) .foundation-symbol::before{background-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20fill%3D%22none%22%20stroke%3D%22%2374E5F5%22%20stroke-width%3D%221.8%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%20viewBox%3D%220%200%2032%2032%22%20aria-hidden%3D%22true%22%20focusable%3D%22false%22%3E%3Cellipse%20cx%3D%2216%22%20cy%3D%227%22%20rx%3D%2210%22%20ry%3D%224%22%2F%3E%3Cpath%20d%3D%22M6%207v18c0%205.5%2020%205.5%2020%200V7M6%2013c0%206%2020%206%2020%200M6%2019c0%206%2020%206%2020%200%22%2F%3E%3C%2Fsvg%3E")}
.site .gf .foundation:nth-child(2) .foundation-symbol::before{background-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20fill%3D%22none%22%20stroke%3D%22%2374E5F5%22%20stroke-width%3D%221.8%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%20viewBox%3D%220%200%2032%2032%22%20aria-hidden%3D%22true%22%20focusable%3D%22false%22%3E%3Cpath%20d%3D%22M16%206a6%206%200%200%200-10%205%206%206%200%200%200-2%209%206%206%200%200%200%208%208c2%200%203-1%204-2%201%201%202%202%204%202a6%206%200%200%200%208-8%206%206%200%200%200-2-9A6%206%200%200%200%2016%206Zm0%200v20M10%2012c3%200%205%202%206%204m6-4c-3%200-5%202-6%204M9%2020c2%200%205-1%207-4m7%204c-2%200-5-1-7-4%22%2F%3E%3C%2Fsvg%3E")}
.site .gf .gf-icon[data-glyph="boundaries"]::before{background-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20focusable%3D%22false%22%20aria-hidden%3D%22true%22%3E%3Cg%20fill%3D%22none%22%20stroke%3D%22%2378DDEB%22%20stroke-width%3D%221.65%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D%22M12%2022s8-4%208-10V5l-8-3-8%203v7c0%206%208%2010%208%2010Z%22%2F%3E%3Cpath%20d%3D%22m9%2012%202%202%204-4%22%2F%3E%3C%2Fg%3E%3C%2Fsvg%3E")}
.site .gf .gf-icon[data-glyph="accountability"]::before{background-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20focusable%3D%22false%22%20aria-hidden%3D%22true%22%3E%3Cg%20fill%3D%22none%22%20stroke%3D%22%2378DDEB%22%20stroke-width%3D%221.65%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Ccircle%20cx%3D%2212%22%20cy%3D%228%22%20r%3D%223.2%22%2F%3E%3Cpath%20d%3D%22M5.5%2021v-2a6.5%206.5%200%200%201%2013%200v2%22%2F%3E%3Cpath%20d%3D%22m17.5%205%201.6%201.6L22%203.7%22%2F%3E%3C%2Fg%3E%3C%2Fsvg%3E")}
.site .gf .gf-icon[data-glyph="evidence"]::before{background-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20focusable%3D%22false%22%20aria-hidden%3D%22true%22%3E%3Cg%20fill%3D%22none%22%20stroke%3D%22%2378DDEB%22%20stroke-width%3D%221.65%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Crect%20x%3D%225%22%20y%3D%224%22%20width%3D%2214%22%20height%3D%2217%22%20rx%3D%222%22%2F%3E%3Cpath%20d%3D%22M9%204.5h6M8.5%2010h7M8.5%2014h4%22%2F%3E%3Cpath%20d%3D%22m14%2017%201.5%201.5%202.5-3%22%2F%3E%3C%2Fg%3E%3C%2Fsvg%3E")}
.site .gf .gf-icon[data-glyph="traceability"]::before{background-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20focusable%3D%22false%22%20aria-hidden%3D%22true%22%3E%3Cg%20fill%3D%22none%22%20stroke%3D%22%2378DDEB%22%20stroke-width%3D%221.65%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D%22M3%2012a9%209%200%201%200%202.6-6.4%22%2F%3E%3Cpath%20d%3D%22M3%204v5h5%22%2F%3E%3Cpath%20d%3D%22M12%207v5l3%202%22%2F%3E%3C%2Fg%3E%3C%2Fsvg%3E")}
.site .gf .gf-icon[data-glyph="executive-decision"]::before{background-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20focusable%3D%22false%22%20aria-hidden%3D%22true%22%3E%3Cg%20fill%3D%22none%22%20stroke%3D%22%2383E7EE%22%20stroke-width%3D%221.65%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D%22M4%206h16M12%203v18M8%206%204%2013h8L8%206ZM16%206l-4%207h8l-4-7ZM4%2013c.5%202.5%207.5%202.5%208%200M12%2013c.5%202.5%207.5%202.5%208%200M7%2021h10%22%2F%3E%3C%2Fg%3E%3C%2Fsvg%3E")}
.site .gf .gf-icon[data-glyph="trusted-inputs"]::before{background-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20focusable%3D%22false%22%20aria-hidden%3D%22true%22%3E%3Cg%20fill%3D%22none%22%20stroke%3D%22%2378DDEB%22%20stroke-width%3D%221.65%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cellipse%20cx%3D%2212%22%20cy%3D%225%22%20rx%3D%228.5%22%20ry%3D%223%22%2F%3E%3Cpath%20d%3D%22M3.5%205v13c0%204%2017%204%2017%200V5M3.5%2011c0%204%2017%204%2017%200%22%2F%3E%3Cpath%20d%3D%22m9.5%2016%201.6%201.6%203.7-3.7%22%2F%3E%3C%2Fg%3E%3C%2Fsvg%3E")}
.site .gf .gf-icon[data-glyph="decision-ownership"]::before{background-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20focusable%3D%22false%22%20aria-hidden%3D%22true%22%3E%3Cg%20fill%3D%22none%22%20stroke%3D%22%2378DDEB%22%20stroke-width%3D%221.65%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Ccircle%20cx%3D%229%22%20cy%3D%227.6%22%20r%3D%223%22%2F%3E%3Cpath%20d%3D%22M3%2019v-1a6%206%200%200%201%2012%200v1M15.5%2012.5h5m-2.5-2.5v5%22%2F%3E%3C%2Fg%3E%3C%2Fsvg%3E")}
.site .gf .gf-icon[data-glyph="control-by-consequence"]::before{background-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20focusable%3D%22false%22%20aria-hidden%3D%22true%22%3E%3Cg%20fill%3D%22none%22%20stroke%3D%22%2378DDEB%22%20stroke-width%3D%221.65%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D%22m12%203%209%2016a2%202%200%200%201-2%202H5a2%202%200%200%201-2-2l9-16Z%22%2F%3E%3Cpath%20d%3D%22M12%209v4M12%2017h.01%22%2F%3E%3C%2Fg%3E%3C%2Fsvg%3E")}
.site .gf .gf-icon[data-glyph="traceable-outcomes"]::before{background-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20focusable%3D%22false%22%20aria-hidden%3D%22true%22%3E%3Cg%20fill%3D%22none%22%20stroke%3D%22%2378DDEB%22%20stroke-width%3D%221.65%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D%22M7%203h8l4%204v14H7z%22%2F%3E%3Cpath%20d%3D%22M15%203v5h5M10%2012h6M10%2016h4M10%2020h5%22%2F%3E%3Cpath%20d%3D%22M3%208v11%22%2F%3E%3C%2Fg%3E%3C%2Fsvg%3E")}
.site .gf .gf-icon[data-glyph="monitoring-after-launch"]::before{background-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20focusable%3D%22false%22%20aria-hidden%3D%22true%22%3E%3Cg%20fill%3D%22none%22%20stroke%3D%22%2378DDEB%22%20stroke-width%3D%221.65%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D%22M2%2012h4l3-5%204%2010%203-5h6%22%2F%3E%3Ccircle%20cx%3D%2212%22%20cy%3D%2212%22%20r%3D%2210%22%20stroke-dasharray%3D%223%206%22%2F%3E%3C%2Fg%3E%3C%2Fsvg%3E")}
.site .gf .gf-icon[data-glyph="material-change-review"]::before{background-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20focusable%3D%22false%22%20aria-hidden%3D%22true%22%3E%3Cg%20fill%3D%22none%22%20stroke%3D%22%2378DDEB%22%20stroke-width%3D%221.65%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D%22M3%2011a9%209%200%200%201%2016-5l2%202%22%2F%3E%3Cpath%20d%3D%22M21%203v5h-5M21%2013a9%209%200%200%201-16%205l-2-2M3%2021v-5h5%22%2F%3E%3C%2Fg%3E%3C%2Fsvg%3E")}
.site .gf .gf-icon[data-glyph="know"]::before{background-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20focusable%3D%22false%22%20aria-hidden%3D%22true%22%3E%3Cg%20fill%3D%22none%22%20stroke%3D%22%2378DDEB%22%20stroke-width%3D%221.65%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D%22M3%2010%205%205l3-1%202%204M14%208l2-4%203%201%202%205%22%2F%3E%3Ccircle%20cx%3D%227.5%22%20cy%3D%2214%22%20r%3D%225%22%2F%3E%3Ccircle%20cx%3D%2216.5%22%20cy%3D%2214%22%20r%3D%225%22%2F%3E%3Cpath%20d%3D%22M12.5%2012.5h-1%22%2F%3E%3C%2Fg%3E%3C%2Fsvg%3E")}
.site .gf .gf-icon[data-glyph="own"]::before{background-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20focusable%3D%22false%22%20aria-hidden%3D%22true%22%3E%3Cg%20fill%3D%22none%22%20stroke%3D%22%2378DDEB%22%20stroke-width%3D%221.65%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Ccircle%20cx%3D%2212%22%20cy%3D%227%22%20r%3D%223%22%2F%3E%3Cpath%20d%3D%22M4%2021v-2a8%208%200%200%201%2016%200v2M4%2011c-2%201-3%203-3%205M20%2011c2%201%203%203%203%205%22%2F%3E%3C%2Fg%3E%3C%2Fsvg%3E")}
.site .gf .gf-icon[data-glyph="explain"]::before{background-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20focusable%3D%22false%22%20aria-hidden%3D%22true%22%3E%3Cg%20fill%3D%22none%22%20stroke%3D%22%2378DDEB%22%20stroke-width%3D%221.65%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D%22m12%202%209%205-9%205-9-5%209-5ZM3%2012l9%205%209-5M3%2017l9%205%209-5%22%2F%3E%3C%2Fg%3E%3C%2Fsvg%3E")}
.site .gf .gf-icon[data-glyph="respond"]::before{background-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20focusable%3D%22false%22%20aria-hidden%3D%22true%22%3E%3Cg%20fill%3D%22none%22%20stroke%3D%22%2378DDEB%22%20stroke-width%3D%221.65%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D%22m13%202-8%2011h6l-1%209%209-12h-6l1-8Z%22%2F%3E%3C%2Fg%3E%3C%2Fsvg%3E")}
.site .gf .ring{background-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22600%22%20height%3D%22600%22%20viewBox%3D%220%200%20600%20600%22%3E%0A%3Cdefs%3E%3Cmarker%20id%3D%22gov-arrow%22%20markerWidth%3D%227%22%20markerHeight%3D%227%22%20refX%3D%225%22%20refY%3D%223.5%22%20orient%3D%22auto%22%3E%3Cpath%20d%3D%22M0%200%20L7%203.5%20L0%207%20Z%22%20fill%3D%22%2339d4ee%22%2F%3E%3C%2Fmarker%3E%3C%2Fdefs%3E%0A%3Ccircle%20cx%3D%22300%22%20cy%3D%22300%22%20r%3D%22240%22%20fill%3D%22none%22%20stroke%3D%22%232389AD%22%20stroke-width%3D%221.4%22%20stroke-dasharray%3D%225%208%22%20opacity%3D%22.64%22%2F%3E%0A%3Cg%20fill%3D%22none%22%20stroke%3D%22%2339D4EE%22%20stroke-width%3D%223.2%22%20stroke-linecap%3D%22round%22%20opacity%3D%22.76%22%20marker-end%3D%22url(%23gov-arrow)%22%3E%3Cpath%20d%3D%22M370%2069%20A240%20240%200%200%201%20499%20165%22%2F%3E%3Cpath%20d%3D%22M537%20271%20A240%20240%200%200%201%20494%20446%22%2F%3E%3Cpath%20d%3D%22M430%20501%20A240%20240%200%200%201%20234%20533%22%2F%3E%3Cpath%20d%3D%22M166%20501%20A240%20240%200%200%201%2064%20334%22%2F%3E%3Cpath%20d%3D%22M62%20267%20A240%20240%200%200%201%20166%20101%22%2F%3E%3Cpath%20d%3D%22M232%2070%20A240%20240%200%200%201%20270%2062%22%2F%3E%3C%2Fg%3E%0A%3C%2Fsvg%3E");background-repeat:no-repeat;background-position:center;background-size:contain}

/* Authored identity and print-edition action: one compact photo, zero JS or network-at-render graphics. */
.site .gf figcaption .gf-author{display:flex;align-items:center;gap:15px;min-width:0}
.site .gf figcaption .gf-author-byline{min-width:0}
.site .gf figcaption .gf-author-photo{display:block;flex:0 0 58px;width:58px;height:58px;aspect-ratio:1;object-fit:cover;border:3px solid #e7faff;border-radius:50%;background:#15465c;box-shadow:0 0 0 3px rgba(81,189,213,.19)}
.site .gf .gf-download{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:28px;align-items:center;margin-top:24px;padding:clamp(22px,2.4vw,32px);border-radius:17px;border:1px solid rgba(128,210,228,.35);background:linear-gradient(115deg,rgba(27,90,111,.72),rgba(13,60,80,.48)),#092a3d;box-shadow:0 16px 45px rgba(0,5,14,.15)}
.site .gf .gf-download-eyebrow{display:block;margin:0 0 9px;color:#79dff0;font:800 10px/1.3 Inter,Arial,sans-serif;letter-spacing:.14em}
.site .gf .gf-download h3{color:#fff;margin:0 0 8px;font:740 clamp(18px,1.85vw,25px)/1.2 Inter,Arial,sans-serif;letter-spacing:-.02em}
.site .gf .gf-download p{margin:0;max-width:710px;color:#bdd9e5;font:450 13px/1.65 Inter,Arial,sans-serif}
.site .gf .gf-download-cta{display:inline-flex;min-height:69px;align-items:center;justify-content:center;gap:15px;white-space:nowrap;padding:13px 23px;color:#07293d!important;background:linear-gradient(115deg,#c9f5fc,#a4e9f6);border:1px solid #e7fbff;border-radius:11px;text-decoration:none!important;box-shadow:0 7px 24px rgba(3,22,34,.20);transition:background .16s ease,transform .16s ease,box-shadow .16s ease}
.site .gf .gf-download-cta:hover,.site .gf .gf-download-cta:focus-visible{background:#e0faff;box-shadow:0 8px 25px rgba(1,18,31,.25);transform:translateY(-1px);outline-offset:3px}
.site .gf .gf-download-arrow{display:grid;place-items:center;flex:0 0 35px;width:35px;height:35px;border-radius:50%;background:#0a354a;color:#9aeaf8;font:800 23px/1 Inter,Arial,sans-serif}
.site .gf .gf-download-cta strong{display:block;font:850 14px/1.3 Inter,Arial,sans-serif}
.site .gf .gf-download-cta small{display:block;margin-top:4px;color:#33576a;font:650 11px/1.35 Inter,Arial,sans-serif}
@media(max-width:780px){.site .gf .gf-download{grid-template-columns:1fr;gap:18px}.site .gf .gf-download-cta{width:100%;white-space:normal;justify-content:flex-start}}
@media(max-width:480px){.site .gf figcaption .gf-author{gap:10px}.site .gf figcaption .gf-author-photo{width:46px;height:46px;flex-basis:46px;border-width:2px}.site .gf .gf-download{padding:18px}.site .gf .gf-download-cta{padding:13px 15px}.site .gf .gf-download-cta strong{font-size:13px}}
@media(prefers-reduced-motion:reduce){.site .gf .gf-download-cta{transition:none}.site .gf .gf-download-cta:hover{transform:none}}
</style>
<section id="governance-operating-model" class="gf" aria-labelledby="gf-title">
<div class="gw">
<header class="intro"><div><p class="ey">The governance operating system</p><h2 id="gf-title">AI &amp; Data Governance.<br><em>Designed to operate.</em></h2></div>
<p class="deck">A practical operating model for turning trusted data into accountable AI at scale — with clear decision rights, proportionate controls and continuous oversight.</p></header>
<figure class="infographic" aria-label="Executive AI and Data Governance infographic connecting trusted data and AI governance with accountable decisions, a six-stage operating lifecycle, named owners, evidence and continuous assurance">
<div class="meta"><span>Executive operating model</span><span>Jair Ribeiro · AI Leadership</span></div>
<div class="two"><article class="foundation"><div class="foundation-head"><span class="foundation-symbol" aria-hidden="true"></span><h3>Data Governance</h3></div><p>Ownership · Stewardship · Quality · Business definitions · Lineage · Access · Privacy · Retention</p></article><article class="foundation"><div class="foundation-head"><span class="foundation-symbol" aria-hidden="true"></span><h3>AI Governance</h3></div><p>Use-case ownership · Risk classification · Human oversight · System evidence · Transparency · Monitoring · Incident response · Change control</p></article></div>
<div class="converge">Two disciplines, one operating conversation</div>
<div class="account"><b>ACCOUNTABILITY BY DESIGN</b> &nbsp; Business purpose · Trusted data · System behavior · Named decision authority · Evidence</div>
<div class="operating">
<aside class="panel principles"><h3 class="label">01 / Four decision tests</h3><ol><li><div class="gf-icon-row"><span class="gf-icon gf-icon-principle" data-glyph="boundaries" aria-hidden="true"></span><div class="gf-icon-copy"><strong>Boundaries</strong><span>What is the system permitted to do?</span></div></div></li><li><div class="gf-icon-row"><span class="gf-icon gf-icon-principle" data-glyph="accountability" aria-hidden="true"></span><div class="gf-icon-copy"><strong>Accountability</strong><span>Who owns the business consequence?</span></div></div></li><li><div class="gf-icon-row"><span class="gf-icon gf-icon-principle" data-glyph="evidence" aria-hidden="true"></span><div class="gf-icon-copy"><strong>Evidence</strong><span>What proof justifies wider use?</span></div></div></li><li><div class="gf-icon-row"><span class="gf-icon gf-icon-principle" data-glyph="traceability" aria-hidden="true"></span><div class="gf-icon-copy"><strong>Traceability</strong><span>Can outcomes be reconstructed?</span></div></div></li></ol><p class="principle-note">Every material decision needs clear authority, proportionate evidence and a traceable record.</p></aside>
<div class="panel cycle"><h3 class="label">02 / Continuous governance lifecycle</h3><p class="sub">From purpose and risk to accountable operation</p>
<div class="stage">
<div class="ring" aria-hidden="true"></div>
<div class="node" style="--x:50%;--y:10%"><small>01</small><b>Frame</b><span>Purpose and consequence</span></div><div class="node" style="--x:82%;--y:27%"><small>02</small><b>Classify</b><span>Risk and data sensitivity</span></div><div class="node" style="--x:82%;--y:73%"><small>03</small><b>Assign</b><span>Business, technical and data owners</span></div><div class="node" style="--x:50%;--y:90%"><small>04</small><b>Evidence</b><span>Define stage controls and proof</span></div><div class="node" style="--x:18%;--y:73%"><small>05</small><b>Decide</b><span>Release, constrain or stop</span></div><div class="node" style="--x:18%;--y:27%"><small>06</small><b>Monitor</b><span>Learn and reassess</span></div>
<div class="core"><span class="gf-icon gf-icon-core" data-glyph="executive-decision" aria-hidden="true"></span><small>ACCOUNTABLE</small><strong>Executive<br>decision</strong><span>Release · Scale<br>Constrain · Stop</span></div>
</div>
<p class="footnote">Monitor and reassess when a material change means the original approval may no longer apply.</p></div>
<aside class="panel"><h3 class="label">03 / Six decision accountabilities</h3><ul><li><strong>Business owner</strong><span>Purpose, value and business consequence</span></li><li><strong>Data owner / steward</strong><span>Meaning, quality, access and permitted use</span></li><li><strong>Product / technology owner</strong><span>Behavior, security and technical readiness</span></li><li><strong>Appropriate risk authority</strong><span>Residual exposure and escalation</span></li><li><strong>Portfolio / governance authority</strong><span>Scale, constrain, revise or stop</span></li><li><strong>Named operating owner</strong><span>Thresholds, incidents and reassessment</span></li></ul></aside>
</div>
<div class="bottom">
<section class="panel"><h3 class="label">04 / Operating mechanisms</h3><ul><li class="gf-mechanism"><span class="gf-icon gf-icon-mechanism" data-glyph="trusted-inputs" aria-hidden="true"></span><div class="gf-icon-copy"><strong>Trusted inputs</strong><span>Sources, quality, lineage and access</span></div></li><li class="gf-mechanism"><span class="gf-icon gf-icon-mechanism" data-glyph="decision-ownership" aria-hidden="true"></span><div class="gf-icon-copy"><strong>Decision ownership</strong><span>Named authority, decision rights and escalation</span></div></li><li class="gf-mechanism"><span class="gf-icon gf-icon-mechanism" data-glyph="control-by-consequence" aria-hidden="true"></span><div class="gf-icon-copy"><strong>Control by consequence</strong><span>Risk tier, evidence and human oversight</span></div></li><li class="gf-mechanism"><span class="gf-icon gf-icon-mechanism" data-glyph="traceable-outcomes" aria-hidden="true"></span><div class="gf-icon-copy"><strong>Traceable outcomes</strong><span>Versions, sources and decision records</span></div></li><li class="gf-mechanism"><span class="gf-icon gf-icon-mechanism" data-glyph="monitoring-after-launch" aria-hidden="true"></span><div class="gf-icon-copy"><strong>Monitoring after launch</strong><span>Performance, drift and intervention thresholds</span></div></li><li class="gf-mechanism"><span class="gf-icon gf-icon-mechanism" data-glyph="material-change-review" aria-hidden="true"></span><div class="gf-icon-copy"><strong>Material-change review</strong><span>New model, data sources, users or purpose</span></div></li></ul></section>
<section class="panel approval"><h3 class="label">05 / Seven questions before “go”</h3><ol><li><i aria-hidden="true">1</i><div><strong>Purpose</strong><span>What changes — and what if the AI is wrong?</span></div></li><li><i aria-hidden="true">2</i><div><strong>Data</strong><span>Who owns the sources, quality and permitted use?</span></div></li><li><i aria-hidden="true">3</i><div><strong>Accountability</strong><span>Who owns the outcome and who can stop use?</span></div></li><li><i aria-hidden="true">4</i><div><strong>Boundaries</strong><span>What is outside its authority, and where is human judgment required?</span></div></li><li><i aria-hidden="true">5</i><div><strong>Evidence</strong><span>What proof and risk acceptance justify release?</span></div></li><li><i aria-hidden="true">6</i><div><strong>Traceability</strong><span>Could we reconstruct a material outcome?</span></div></li><li><i aria-hidden="true">7</i><div><strong>Monitoring</strong><span>What triggers intervention or reassessment?</span></div></li></ol></section>
<section class="panel response"><h3 class="label">06 / Change and response</h3><ol><li><strong>Detect change</strong><span>Data, behavior, use or context shifts</span></li><li><strong>Escalate</strong><span>Notify the named decision authority</span></li><li><strong>Reassess</strong><span>Revisit controls and approval evidence</span></li><li><strong>Continue · constrain · stop</strong><span>Document the revised decision</span></li></ol></section>
</div>
<div class="signals"><h3>EXECUTIVE ASSURANCE · FOUR OBSERVABLE SIGNALS</h3><div class="four"><div class="gf-signal"><span class="gf-icon gf-icon-signal" data-glyph="know" aria-hidden="true"></span><strong>KNOW</strong><span>Where material AI is used and for which purpose</span></div><div class="gf-signal"><span class="gf-icon gf-icon-signal" data-glyph="own" aria-hidden="true"></span><strong>OWN</strong><span>Named owners for the business, data and system behavior</span></div><div class="gf-signal"><span class="gf-icon gf-icon-signal" data-glyph="explain" aria-hidden="true"></span><strong>EXPLAIN</strong><span>The evidence and decisions behind material outcomes</span></div><div class="gf-signal"><span class="gf-icon gf-icon-signal" data-glyph="respond" aria-hidden="true"></span><strong>RESPOND</strong><span>When to intervene and who can act</span></div></div></div>
<p class="takeaway">Governance is not a one-time approval. It is a continuous system of accountable decisions.</p>
<figcaption><div class="gf-author"><img class="gf-author-photo" src="app/static/governance-avatar.webp" alt="Jair Ribeiro speaking at an executive event" width="60" height="60" loading="lazy" decoding="async"><div class="gf-author-byline"><strong>Jair Ribeiro</strong><small>Enterprise AI Adoption · Governance · Business Transformation</small></div></div><span class="badge">AI LEADER</span></figcaption>
</figure>
<section class="gf-download" aria-label="Download the AI and Data Governance framework">
  <div class="gf-download-info"><span class="gf-download-eyebrow">OFFICIAL FRAMEWORK · PRINT EDITION</span><h3>Keep the operating model at hand.</h3><p>The complete executive visual, formatted for A4 printing and sharing. One-page, high-resolution vector PDF.</p></div>
  <a class="gf-download-cta" href="app/static/ai-data-governance-framework-a4.pdf" download="Jair_Ribeiro_AI_Data_Governance_Framework_A4.pdf" type="application/pdf" data-hq-event="governance_infographic_pdf_download" aria-label="Download the AI and Data Governance infographic as an A4 PDF"><span class="gf-download-arrow" aria-hidden="true">↓</span><span><strong>Download the infographic</strong><small>A4 PDF · Print-ready · Vector quality</small></span></a>
</section>
<div class="after"><p>An operating perspective linking data responsibility, AI use, decision rights and continuous oversight. These are accountable functions, not prescribed job titles.</p><a href="#governance-evidence" data-hq-event="governance_model_experience">Explore the experience behind the model ↗</a></div>
</div></section>'''
