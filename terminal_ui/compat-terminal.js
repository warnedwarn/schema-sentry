import{createAccount,createClient}from'https://esm.sh/genlayer-js@1.1.8';
import{studionet}from'https://esm.sh/genlayer-js@1.1.8/chains';

const ADDRESS='0xF3012A863250ebD5d5163d187d7cF75bF7A00D49';
const ENDPOINT='https://studio.genlayer.com/api';
const PROOF_ID='SS-1788740378';
const DEFAULT_SOURCES=[
 'https://raw.githubusercontent.com/warnedwarn/schema-sentry/dbe721aa80674612693a479f6173f1e17f270640/evidence/old-api.txt',
 'https://cdn.jsdelivr.net/gh/warnedwarn/schema-sentry@dbe721aa80674612693a479f6173f1e17f270640/evidence/new-api.txt',
 'https://github.com/warnedwarn/schema-sentry/raw/dbe721aa80674612693a479f6173f1e17f270640/evidence/migration-policy.txt'
];
const DEFAULT_AUTHORITIES=[
 '0xCAFA30BF94D4fb01146588a1b7901BD85E7DbD0f',
 '0xAD049E0Edc298C97552eD60071a35bfc60181FD4',
 '0x05C0cc3F433F6e296f18117f558FdB9043434793'
];

const root=document.createElement('div');
root.innerHTML=`<style>
.schema-lab{max-width:1180px;margin:30px auto;background:#071118;color:#8affc1;border:1px solid #1c6b50;font:14px ui-monospace,monospace}
.labbar{display:flex;align-items:center;gap:9px;padding:12px 16px;background:#0e1d25;border-bottom:1px solid #1c6b50}.labbar i{width:11px;height:11px;border-radius:50%;background:#ff6b6b}.labbar i:nth-child(2){background:#ffd166}.labbar i:nth-child(3){background:#62e6a5}.labbar b{flex:1}.wallet{border:1px solid #62e6a5!important;background:transparent!important;color:#8affc1!important}
.grid{display:grid;grid-template-columns:1.25fr .9fr}.composer,.console{padding:26px}.console{border-left:1px solid #1c6b50;background:#040b10}.schema-lab h2{margin:0 0 18px;color:#fff}.schema-lab h3{margin:24px 0 8px;color:#fff;font-size:13px;letter-spacing:.08em}
.schema-lab label{display:grid;gap:5px;margin:10px 0;color:#91b5a7}.schema-lab input,.schema-lab select{width:100%;padding:11px;background:#0a1820;color:#d9ffea;border:1px solid #225943}.triplet{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.triplet label{min-width:0}.triplet input{font-size:11px}
.actions{display:flex;flex-wrap:wrap;gap:7px;margin:16px 0}.schema-lab button{padding:11px 14px;background:#62e6a5;color:#03110b;border:0;font-weight:900;cursor:pointer}.schema-lab button:disabled{opacity:.45;cursor:not-allowed}.prompt{padding:14px;background:#000;margin-bottom:14px;color:#fff}.hint{padding:12px;border-left:3px solid #ffd166;color:#d5d6a7}.schema-lab pre{white-space:pre-wrap;word-break:break-word;color:#8affc1;max-height:520px;overflow:auto}.stage{display:flex;gap:6px;flex-wrap:wrap;margin-top:12px}.stage span{border:1px solid #225943;padding:5px 7px;font-size:11px}.proof{color:#7d9aa8}
@media(max-width:900px){.grid,.triplet{grid-template-columns:1fr}.console{border-left:0;border-top:1px solid #1c6b50}}
</style>
<section class="schema-lab">
 <div class="labbar"><i></i><i></i><i></i><b>schema-sentry / revised lifecycle</b><button class="wallet" id="cx">CONNECT WALLET</button></div>
 <div class="grid">
  <div class="composer">
   <h2>FREEZE A COMPATIBILITY REVIEW</h2>
   <label>Review ID<input id="id" value="${PROOF_ID}" placeholder="Use a new unique review ID"></label>
   <label>Service<input id="service" value="Profiles API"></label>
   <label>Revision<input id="rev" value="v2"></label>
   <h3>THREE EDITABLE SOURCE RECORDS</h3>
   <div class="triplet">${DEFAULT_SOURCES.map((x,i)=>`<label>Slot ${i}<input id="source${i}" type="url" value="${x}"></label>`).join('')}</div>
   <h3>THREE SOURCE AUTHORITIES</h3>
   <div class="triplet">${DEFAULT_AUTHORITIES.map((x,i)=>`<label>Authority ${i}<input id="authority${i}" value="${x}"></label>`).join('')}</div>
   <label>Release controller<input id="controller" value="${DEFAULT_AUTHORITIES[2]}"></label>
   <div class="actions"><button id="register">REGISTER + FREEZE</button><button id="load">LOAD CANONICAL REVIEW</button></div>
   <h3>AUTHORITY ATTESTATION</h3>
   <div class="triplet"><label>Source slot<select id="slot"><option value="0">0</option><option value="1">1</option><option value="2">2</option></select></label><label style="grid-column:span 2">Frozen digest<input id="digest" placeholder="Load the review to select its digest"></label></div>
   <div class="actions"><button id="attest">ATTEST SOURCE DIGEST</button><button id="review">RUN COMPATIBILITY REVIEW</button><button id="release">EXECUTE RELEASE</button></div>
   <p class="hint">Register with the owner wallet. Switch to the matching authority wallet for each slot. Only the configured release controller can execute an APPROVED release.</p>
  </div>
  <aside class="console">
   <div class="prompt">$ schema-sentry lifecycle --canonical</div>
   <p class="proof">Verified proof: ${PROOF_ID}</p>
   <div class="stage"><span>SUBMITTED</span><span>ACCEPTED</span><span>FINALIZED</span><span>MAJORITY_AGREE</span></div>
   <pre id="state">Load the verified proof or enter a fresh review ID.</pre>
  </aside>
 </div>
</section>`;
document.body.replaceChildren(root);

const q=x=>root.querySelector(x),value=x=>q('#'+x).value.trim();
const reader=createClient({chain:studionet,endpoint:ENDPOINT,account:createAccount()});
let wallet=null,account='',current=null;
const show=x=>q('#state').textContent=typeof x==='string'?x:JSON.stringify(x,(_,z)=>typeof z==='bigint'?z.toString():z,2);
const execution=r=>String(r?.txExecutionResultName??r?.tx_execution_result??r?.tx_execution_result_name??'').toUpperCase();

async function connect(){
 const provider=window.ethereum;if(!provider)throw Error('Install MetaMask or Rabby to write.');
 [account]=await provider.request({method:'eth_requestAccounts'});
 if(String(await provider.request({method:'eth_chainId'})).toLowerCase()!=='0xf22f')await provider.request({method:'wallet_switchEthereumChain',params:[{chainId:'0xf22f'}]});
 wallet=createClient({chain:studionet,endpoint:ENDPOINT,account,provider});
 await wallet.connect('studionet');
 q('#cx').textContent=account.slice(0,6)+'…'+account.slice(-4);
 show('Wallet connected to StudioNet as '+account);
}
async function load(){
 const id=value('id');if(!id)throw Error('Enter a review ID.');
 current=await reader.readContract({address:ADDRESS,functionName:'get_review',args:[id]});
 const slot=Number(value('slot'));q('#digest').value=current.digests?.[slot]||'';
 show(current);return current;
}
async function finalized(hash,label){
 show('SUBMITTED '+hash+'\nWaiting for ACCEPTED...');
 const accepted=await wallet.waitForTransactionReceipt({hash,status:'ACCEPTED',retries:120,interval:5000});
 const early=execution(accepted);if(early&&!['SUCCESS','FINISHED_WITH_RETURN','1'].includes(early))throw Error(label+' failed at acceptance: '+early);
 show('ACCEPTED '+hash+'\nWaiting for FINALIZED validator consensus...');
 const receipt=await wallet.waitForTransactionReceipt({hash,status:'FINALIZED',retries:120,interval:5000});
 const consensus=String(receipt?.result_name??receipt?.resultName??'').toUpperCase(),result=execution(receipt);
 if(consensus!=='MAJORITY_AGREE')throw Error(label+' finalized without MAJORITY_AGREE: '+(consensus||'UNKNOWN'));
 if(result&&!['SUCCESS','FINISHED_WITH_RETURN','1'].includes(result))throw Error(label+' failed: '+result);
 return receipt;
}
async function act(button,method,args){
 const original=button.textContent;button.disabled=true;
 try{if(!wallet)await connect();button.textContent='CONFIRM IN WALLET';const hash=await wallet.writeContract({address:ADDRESS,functionName:method,args,value:0n});button.textContent='WAITING FOR FINALITY';await finalized(hash,method);await load();show(q('#state').textContent+'\n\n'+method+' TX: '+hash+'\nFINALIZED / MAJORITY_AGREE / SUCCESS');}
 catch(error){show(error?.message||String(error));}
 finally{button.disabled=false;button.textContent=original;}
}
q('#cx').onclick=()=>connect().catch(error=>show(error?.message||String(error)));
q('#load').onclick=()=>load().catch(error=>show(error?.message||String(error)));
q('#slot').onchange=()=>{if(current)q('#digest').value=current.digests?.[Number(value('slot'))]||''};
q('#register').onclick=()=>act(q('#register'),'register',[value('id'),value('service'),value('rev'),[0,1,2].map(i=>value('source'+i)),[0,1,2].map(i=>value('authority'+i)),value('controller')]);
q('#attest').onclick=()=>act(q('#attest'),'attest_source',[value('id'),BigInt(value('slot')),value('digest')]);
q('#review').onclick=()=>act(q('#review'),'review',[value('id')]);
q('#release').onclick=()=>act(q('#release'),'execute_release',[value('id')]);