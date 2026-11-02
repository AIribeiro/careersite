"""Editorial landing-page skin, scoped to the Executive AI Briefings collection.

The first-party CSS works with Streamlit st.html sanitization. No external
fonts, JavaScript, SVG, image hosting, or third-party components are needed.
"""

PREMIUM_BRIEFINGS_CSS = r'''<style>
/* 2026 editorial collection — all selectors scoped to the portfolio site. */
.site .be-hero{position:relative;isolation:isolate;overflow:hidden;padding:clamp(64px,7vw,112px) 0 clamp(52px,6vw,86px);background:radial-gradient(ellipse at 85% 22%,rgba(51,97,112,.45) 0%,transparent 38%),radial-gradient(ellipse at 12% 84%,rgba(126,78,57,.16) 0%,transparent 46%),#0d2031;color:#f5f1e9}
.site .be-hero:before{content:"";position:absolute;inset:0;z-index:-1;opacity:.35;background:linear-gradient(90deg,transparent calc(100% - 1px),rgba(193,209,215,.09) 100%);background-size:84px 84px;pointer-events:none}
.site .be-hero:after{content:"";position:absolute;top:-22%;right:-17%;width:min(70vw,850px);aspect-ratio:1;border:1px solid rgba(238,189,151,.1);border-radius:50%;box-shadow:0 0 0 85px rgba(219,160,115,.018),0 0 0 174px rgba(219,160,115,.018);z-index:-1;pointer-events:none}
.site .be-hero-inner{display:grid;grid-template-columns:minmax(0,1.12fr) minmax(310px,.88fr);gap:clamp(30px,5vw,85px);align-items:center}
.site .be-eyebrow{display:inline-flex;align-items:center;gap:13px;margin:0;color:#dcb596;font:800 10px/1.5 Arial,sans-serif;letter-spacing:.20em;text-transform:uppercase}
.site .be-eyebrow:before{content:"";display:inline-block;width:25px;height:1px;background:#d6aa84}
.site .be-hero h1{max-width:800px;margin:29px 0 22px;color:#fff9f1;font:400 clamp(49px,6.3vw,88px)/1.025 Georgia,"Times New Roman",serif;letter-spacing:-.052em;text-wrap:balance}
.site .be-hero h1 em{font-weight:400;color:#dcb28f;font-style:italic}
.site .be-hero-deck{max-width:630px;margin:0;color:#d2d9dc;font:400 clamp(15px,1.46vw,18px)/1.75 Arial,sans-serif}
.site .be-hero-actions{display:flex;flex-wrap:wrap;align-items:center;gap:12px 27px;margin-top:32px}
.site .be-primary-action{display:inline-flex;gap:15px;align-items:center;justify-content:center;min-height:47px;padding:13px 21px;background:#eac4a5;border:1px solid #eac4a5;color:#12273a!important;text-decoration:none!important;font:800 12px/1.35 Arial,sans-serif;transition:background .2s ease,transform .2s ease}
.site .be-primary-action:hover,.site .be-primary-action:focus-visible{background:#f8e2cf;transform:translateY(-2px)}
.site .be-text-action{display:inline-flex;align-items:center;gap:12px;color:#e8e4e0!important;text-decoration:none!important;border-bottom:1px solid rgba(231,189,157,.52);padding:10px 0;font:750 12px/1.4 Arial,sans-serif}
.site .be-text-action:hover{text-decoration:none!important;color:#fff!important;border-color:#fff}
.site .be-hero-attribution{margin:42px 0 0;padding-top:19px;border-top:1px solid rgba(228,202,176,.19);max-width:520px;color:#a9bdc8;font:700 10px/1.6 Arial,sans-serif;letter-spacing:.1em;text-transform:uppercase}
.site .be-hero-attribution strong{color:#eac4a5;font-weight:800}
.site .be-lens{position:relative;min-width:0;padding:28px 28px 23px;border:1px solid rgba(224,186,154,.38);background:linear-gradient(155deg,rgba(34,69,82,.72),rgba(11,31,48,.95) 72%);box-shadow:0 30px 76px rgba(0,9,19,.24)}
.site .be-lens-header{display:flex;justify-content:space-between;align-items:center;gap:16px;border-bottom:1px solid rgba(210,223,227,.19);padding-bottom:19px;color:#e9bc98;font:800 10px/1.5 Arial,sans-serif;letter-spacing:.14em;text-transform:uppercase}
.site .be-lens-header span:last-child{color:#95aeba;letter-spacing:.08em}
.site .be-lens-title{font:400 clamp(25px,2.6vw,36px)/1.2 Georgia,serif;margin:24px 0 24px;color:#f7f1eb;letter-spacing:-.018em}
.site .be-lens-steps{list-style:none;margin:0;padding:0;border-top:1px solid rgba(217,230,232,.14)}
.site .be-lens-steps li{display:grid;grid-template-columns:39px 1fr;gap:18px;align-items:start;padding:15px 0;border-bottom:1px solid rgba(217,230,232,.14)}
.site .be-lens-steps b{color:#e5b893;font:600 23px/1 Georgia,serif}
.site .be-lens-steps strong{display:block;color:#f3f0ed;font:750 13px/1.35 Arial,sans-serif}
.site .be-lens-steps p{margin:5px 0 0;color:#b6c8d1;font:400 11px/1.6 Arial,sans-serif}
.site .be-lens-footer{display:flex;justify-content:space-between;gap:18px;flex-wrap:wrap;margin-top:22px;color:#a6b6bf;font:750 9px/1.5 Arial,sans-serif;letter-spacing:.12em;text-transform:uppercase}
.site .be-lens-footer span:first-child{color:#deb08c}
.site .be-bridge{background:#eae4d9;border-bottom:1px solid #d8d0c6}
.site .be-bridge-inner{display:grid;grid-template-columns:1.3fr repeat(3,.85fr);gap:0;align-items:stretch}
.site .be-bridge-label{display:flex;align-items:center;padding:25px 25px 25px 0;color:#243747;font:400 24px/1.22 Georgia,serif;letter-spacing:-.018em}
.site .be-bridge-item{display:flex;flex-direction:column;justify-content:center;padding:22px 18px;border-left:1px solid #d0c6b9}
.site .be-bridge-item b{color:#aa734e;font:800 9px/1.4 Arial,sans-serif;letter-spacing:.15em}
.site .be-bridge-item span{color:#263849;font:750 12px/1.45 Arial,sans-serif;margin-top:6px}
.site .be-collection{padding:clamp(50px,6vw,83px) 0 clamp(68px,7vw,103px);background:#f7f4ee}
.site .be-section-heading{display:flex;align-items:end;justify-content:space-between;gap:20px;margin-bottom:25px}
.site .be-section-heading .briefings-index{letter-spacing:.18em;color:#9c5f41}
.site .be-section-heading h2{font:400 clamp(32px,4.2vw,53px)/1.11 Georgia,serif;letter-spacing:-.037em;color:#1b3041;margin:8px 0 0}
.site .be-section-heading p{max-width:290px;color:#61717c;font:400 13px/1.55 Arial,sans-serif;margin:0 0 3px}
.site .be-feature{margin:0 0 57px}
.site .be-feature .briefings-library-card{display:grid;grid-template-columns:minmax(0,1.08fr) minmax(290px,.92fr);min-height:370px;overflow:hidden;background:#fffdfa;border:1px solid #d8d3ca;box-shadow:0 18px 44px rgba(21,35,48,.09);color:#182c3f!important;text-decoration:none!important;transition:border-color .2s ease,box-shadow .2s ease,transform .2s ease}
.site .be-feature .briefings-library-card:hover,.site .be-feature .briefings-library-card:focus-visible{border-color:#ae7957;transform:translateY(-3px);box-shadow:0 25px 60px rgba(21,35,48,.14)}
.site .be-feature .briefings-library-card:focus-visible,.site .be-collection .briefings-library-card:focus-visible{outline:3px solid #ae7957;outline-offset:4px}
.site .be-feature-copy{display:flex;flex-direction:column;min-width:0;padding:clamp(28px,3.6vw,51px)}
.site .be-feature-top{display:flex;justify-content:space-between;flex-wrap:wrap;gap:10px;color:#a26947;font:800 10px/1.45 Arial,sans-serif;letter-spacing:.13em;text-transform:uppercase}
.site .be-feature-top span:last-child{color:#71808a}
.site .be-feature h3{max-width:590px;color:#1c3346;font:400 clamp(31px,3.35vw,46px)/1.11 Georgia,serif;letter-spacing:-.031em;margin:27px 0 17px}
.site .be-feature-copy>p{color:#52616c;font:400 15px/1.68 Arial,sans-serif;max-width:585px;margin:0 0 26px}
.site .be-feature-bottom{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;margin-top:auto;border-top:1px solid #e3ded5;padding-top:21px;color:#64717a;font:700 11px/1.5 Arial,sans-serif}
.site .be-feature-bottom strong{display:flex;align-items:center;gap:9px;color:#a25c3a;font:800 12px/1.4 Arial,sans-serif}
.site .be-feature-art{display:flex;min-height:0;background:#112b3d;position:relative;overflow:hidden}
.site .be-feature-art .briefings-catalog-art{height:100%;min-height:370px;padding:clamp(23px,3.3vw,42px);gap:23px;justify-content:space-between}
.site .be-feature-art .briefings-catalog-art:after{inset:17px}
.site .be-feature-art .briefings-catalog-art-kicker{font-size:10px}
.site .be-feature-art .aia-art-steps{grid-template-columns:1fr;max-width:390px;gap:9px}
.site .be-feature-art .aia-art-steps span{padding:11px 15px}
.site .be-feature-art .aia-art-steps b{display:inline;margin:0 13px 0 0}
.site .be-feature-art .briefings-art-options{grid-template-columns:1fr;max-width:320px}
.site .be-feature-art .briefings-governance-art{max-width:390px}
.site .be-collection-subheading{display:flex;justify-content:space-between;gap:18px;align-items:baseline;border-bottom:1px solid #dcd5cb;padding-bottom:17px;margin-bottom:22px}
.site .be-collection-subheading h2{margin:0;color:#203648;font:400 clamp(29px,3.5vw,42px)/1.16 Georgia,serif;letter-spacing:-.03em}
.site .be-collection-subheading span{color:#75726b;font:750 10px/1.5 Arial,sans-serif;white-space:nowrap;letter-spacing:.07em;text-transform:uppercase}
.site .be-collection .briefings-library-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:17px;align-items:stretch}
.site .be-collection .briefings-library-card{min-width:0;display:flex;flex-direction:column;overflow:hidden;text-decoration:none!important;border:1px solid #dcd9d2;background:#fffdfa;color:#1c3143!important;box-shadow:0 9px 20px rgba(21,35,48,.036);transition:transform .2s,border-color .2s,box-shadow .2s}
.site .be-collection .briefings-library-card:hover{transform:translateY(-4px);border-color:#b27b58;box-shadow:0 18px 38px rgba(21,35,48,.09)}
.site .be-card-art{height:142px;overflow:hidden;background:#15364b}
.site .be-card-art .briefings-catalog-art{height:142px;padding:17px 20px;gap:10px}
.site .be-card-art .briefings-catalog-art:after{inset:9px}
.site .be-card-art .briefings-catalog-art-kicker{font-size:8px}
.site .be-card-art .briefings-art-options{gap:5px}
.site .be-card-art .briefings-art-options span{min-height:36px;font-size:11px}
.site .be-card-art .briefings-art-numbers{gap:5px}
.site .be-card-art .briefings-art-numbers b{width:25px;height:32px;font-size:11px}
.site .be-card-art .aia-art-steps{gap:5px}
.site .be-card-art .aia-art-steps span{font-size:10px;padding:7px}
.site .be-card-art .briefings-governance-art{gap:5px}
.site .be-card-art .briefings-art-generic{font-size:27px}
.site .be-card-art .briefings-art-connector,.site .be-card-art .briefings-art-label,.site .be-card-art .aia-art-foot,.site .be-card-art .briefings-governance-art-rule{font-size:9px}
.site .be-card-copy{flex:1;display:flex;flex-direction:column;min-width:0;padding:25px 25px 23px}
.site .be-card-meta{display:flex;justify-content:space-between;gap:9px;color:#9a603f;font:800 9px/1.5 Arial,sans-serif;letter-spacing:.10em;text-transform:uppercase}
.site .be-card-meta span:last-child{color:#78828a}
.site .be-card-copy h3{color:#203548;font:400 clamp(24px,2.35vw,31px)/1.19 Georgia,serif;letter-spacing:-.023em;margin:17px 0 12px;overflow-wrap:anywhere}
.site .be-card-copy>p{margin:0 0 26px;color:#556571;font:400 13px/1.64 Arial,sans-serif}
.site .be-card-footer{margin-top:auto;padding-top:16px;border-top:1px solid #e7e1d8;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:9px;color:#667682;font:700 10px/1.5 Arial,sans-serif}
.site .be-card-footer strong{color:#a15f3c;font:800 11px/1.4 Arial,sans-serif}
.site .be-empty{padding:35px;border:1px solid #d7d2c9;background:#fffdfa;color:#4a5b68;font:400 14px/1.7 Arial,sans-serif}
.site .be-empty strong{color:#24394b;display:block;font:400 28px/1.2 Georgia,serif;margin-bottom:10px}
.site .be-afterword{margin-top:50px;padding:22px 0 0;border-top:1px solid #dcd5ca;display:flex;justify-content:space-between;gap:20px;align-items:center}
.site .be-afterword p{margin:0;max-width:690px;color:#5d6b74;font:400 13px/1.65 Arial,sans-serif}
.site .be-afterword strong{color:#243747;font-weight:800}
.site .be-afterword a{font:800 12px/1.5 Arial,sans-serif;color:#945633!important;text-decoration:none!important;border-bottom:1px solid #b77c57;white-space:nowrap;padding-bottom:5px}
@media(max-width:1050px){.site .be-hero-inner{grid-template-columns:1fr}.site .be-hero h1{max-width:780px}.site .be-lens{max-width:750px}.site .be-bridge-inner{grid-template-columns:repeat(3,1fr)}.site .be-bridge-label{grid-column:1/-1;padding-bottom:7px}.site .be-bridge-item:first-of-type{border-left:0;padding-left:0}.site .be-collection .briefings-library-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:740px){.site .be-hero{padding:55px 0 53px}.site .be-hero-inner{gap:32px}.site .be-hero h1{font-size:clamp(43px,10vw,64px);margin:23px 0 18px}.site .be-hero-deck{font-size:15px}.site .be-hero-attribution{margin-top:26px}.site .be-lens{padding:22px}.site .be-bridge-inner{grid-template-columns:1fr}.site .be-bridge-label{padding:23px 0 8px}.site .be-bridge-item,.site .be-bridge-item:first-of-type{padding:12px 0;border-left:0;border-top:1px solid #d2c7b8}.site .be-collection{padding:45px 0 68px}.site .be-section-heading{display:block}.site .be-section-heading p{margin-top:13px}.site .be-feature{margin-bottom:46px}.site .be-feature .briefings-library-card{grid-template-columns:1fr}.site .be-feature-copy{padding:25px;min-height:330px}.site .be-feature h3{font-size:36px;margin:20px 0 14px}.site .be-feature-art{order:-1}.site .be-feature-art .briefings-catalog-art{height:210px;min-height:210px;padding:22px}.site .be-feature-art .aia-art-steps{grid-template-columns:repeat(3,minmax(0,1fr))}.site .be-feature-art .aia-art-steps b{display:block;margin:0 0 5px}.site .be-collection .briefings-library-grid{grid-template-columns:1fr}.site .be-card-art{height:153px}.site .be-card-art .briefings-catalog-art{height:153px}.site .be-collection-subheading{align-items:flex-end}.site .be-afterword{display:block}.site .be-afterword a{display:inline-block;margin-top:18px}}
@media(max-width:420px){.site .be-hero h1{font-size:42px}.site .be-eyebrow{font-size:9px;letter-spacing:.14em}.site .be-lens-title{font-size:27px}.site .be-feature-top{font-size:9px}.site .be-feature h3{font-size:32px}.site .be-collection-subheading{display:block}.site .be-collection-subheading span{display:block;margin-top:8px}.site .be-feature-art .aia-art-steps span{font-size:10px;padding:8px}.site .be-feature-art .aia-art-steps b{margin-bottom:4px}}
@media(prefers-reduced-motion:reduce){.site .be-primary-action,.site .be-collection .briefings-library-card,.site .be-feature .briefings-library-card{transition:none;transform:none!important}}
</style>'''
