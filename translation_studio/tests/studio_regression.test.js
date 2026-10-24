// REG Translation Studio non-regression: node tests/studio_regression.test.js preview/index.html
const {JSDOM,VirtualConsole}=require('jsdom');
const fs=require('node:fs');
const path=process.argv[2] || 'preview/index.html';
const html=fs.readFileSync(path,'utf8').replace(/<link[^>]*>/,'');
let fails=0;
const ok=(c,m)=>{console.log((c?'PASS ':'FAIL ')+m);if(!c)fails++;};
function page(){
  const errs=[];const vc=new VirtualConsole();
  vc.on('jsdomError',e=>errs.push(e.message));
  const w=new JSDOM(html,{runScripts:'dangerously',url:'http://localhost/',virtualConsole:vc,
    beforeParse(w){w.HTMLElement.prototype.scrollIntoView=()=>{};}}).window;
  return {w,d:w.document,errs};
}
function run(l0,dom,mode){
  const {w,d,errs}=page();
  d.getElementById('l0').value=l0;d.getElementById('dom').value=dom;
  if(mode)d.getElementById('mode').value=mode;
  d.getElementById('go').click();
  const t=n=>{
    d.querySelector('.tab[data-t="'+n+'"]').click();
    const p=d.querySelector('#pane pre');
    return p?p.textContent.replace(/Copier$/,''):d.getElementById('pane').textContent;
  };
  return {w,d,errs,banner:d.getElementById('banner').textContent,
    yaml:t('yaml'),py:t('py'),api:t('api'),t};
}
const A=run('Ne jamais exécuter deux fois un règlement si la latence système dépasse 200 ms.','FINANCIAL_EXECUTION');
ok(A.errs.length===0,'chargement sans erreur JS '+A.errs.join(';'));
ok(/propriétés candidates non admises/.test(A.d.querySelector('.sub').textContent),'intro : aucune compilation de profil admis');
ok(!/compile en profil REG\+/.test(A.d.querySelector('.sub').textContent),'intro : promesse de compilation retirée');
ok(/\(latency_ms > 200\) => not already_executed/.test(A.yaml),'règlement : condition si latence > 200 conservée');
ok(!/amount/.test(A.yaml),'règlement : aucun plafond de montant inventé');
ok(!/RESOLVED/.test(A.yaml+A.api)&&!/Résolu/.test(A.banner),'règlement : jamais RESOLVED / Résolu');
const B=run('Tout paiement supérieur à 50 000 MAD exige une approbation humaine avant exécution.','AUTONOMOUS_AGENTS');
ok(/\(amount > 50000\) => human_approved == true/.test(B.yaml),'approbation humaine uniquement au-dessus de 50 000 MAD');
ok(!/formula: "amount <= 50000"/.test(B.yaml),'pas de plafond inconditionnel inventé');
const C=run('Les données clients ne doivent jamais quitter la région autorisée, et chaque accès doit être journalisé.','DATA_SOVEREIGNTY');
ok(/CAND_DATA_RESIDENCY/.test(C.yaml)&&/CAND_AUDIT_TRAIL/.test(C.yaml),'résidence ET audit conservés');
const D=run('Les agents doivent adopter un ton bienveillant et ne jamais mentionner Acme Corp aux clients.','ADVISORY_ANALYTICS');
ok(/Hors catalogue/.test(D.banner)&&JSON.parse(D.api).status==='UNMAPPED_PATTERN_GENERATED','hors catalogue : non vérifié');
ok(JSON.parse(D.api).github_issue.status==='PRIVATE_ROUTING_NOT_PERFORMED','mode par défaut : privé');
const E=run('Les agents doivent adopter un ton bienveillant et ne jamais mentionner Acme Corp aux clients.','ADVISORY_ANALYTICS','PUBLIC_COMMUNITY');
E.d.querySelector('.tab[data-t=rfc]').click();
const link=E.d.querySelector('#pane a.btn');
const consent=E.d.querySelector('#pane input[type=checkbox]');
ok(!!(link&&link.hidden&&consent),'lien GitHub masqué avant consentement');
if(consent&&link){consent.checked=true;consent.dispatchEvent(new E.w.Event('change'));}
ok(!!(link&&!link.hidden),'lien visible après consentement explicite');
ok(!/Acme|Corp|@|\\b\\d{2,3}\\b/.test(link?.href||''),'RFC sans texte ni entités utilisateur');
ok(/EXPÉRIMENTAL/.test(A.py),'code Python marqué expérimental');
ok(!/I8_LATENCY|I2_AUDIT|I3_IDEMP|I5_AMOUNT|I11_HUMAN|I14_DATA/.test(A.yaml+B.yaml+C.yaml),'aucun identifiant canonique réutilisé');
ok(run('Ne jamais exécuter deux fois un règlement si la latence système dépasse 200 ms.','FINANCIAL_EXECUTION').yaml===A.yaml,'déterminisme : même entrée, même sortie');
ok(!/TenirBaseProfile|Verdict\.ALLOW/.test(A.py)&&/NotImplementedError/.test(A.py),'aucune interface runtime fictive ni autorisation');
ok(A.errs.length+B.errs.length+C.errs.length+D.errs.length+E.errs.length===0,'aucune erreur JS');
console.log(fails?'\n'+fails+' échec(s)':'\nTout passe');
process.exit(fails?1:0);
