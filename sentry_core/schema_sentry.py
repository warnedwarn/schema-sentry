# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""SchemaSentry: multi-authority schema freeze with an enforceable release gate."""
from genlayer import *
from dataclasses import dataclass
from urllib.parse import urlsplit,unquote
import hashlib,json

EXPECTED='[EXPECTED]';EXTERNAL='[EXTERNAL]';TRANSIENT='[TRANSIENT]';LLM='[LLM_ERROR]'
VERDICTS=('COMPATIBLE','MIGRATION_REQUIRED','BLOCKED','INSUFFICIENT')
def c(value,limit=1000):return str(value).strip()[:limit]
def ident(value):
 key=c(value,72).upper()
 if not key:raise gl.vm.UserError(EXPECTED+' review id required')
 return key
def link(value):
 raw=c(value,500);parts=urlsplit(raw)
 if parts.scheme.lower()!='https' or not parts.hostname or parts.username or parts.password or parts.fragment:raise gl.vm.UserError(EXPECTED+' valid HTTPS source')
 host=parts.hostname.lower().rstrip('.')
 try:port=parts.port
 except:raise gl.vm.UserError(EXPECTED+' valid HTTPS source')
 path=unquote(parts.path or '/')
 if any(piece in ('.','..') for piece in path.split('/')):raise gl.vm.UserError(EXPECTED+' normalized HTTPS path required')
 return raw,host+((':'+str(port)) if port and port!=443 else '')
def obj(value):
 if isinstance(value,dict):return value
 text=str(value);start=text.find('{');end=text.rfind('}')
 if start<0 or end<=start:raise gl.vm.UserError(LLM+' invalid JSON')
 try:return json.loads(text[start:end+1])
 except:raise gl.vm.UserError(LLM+' invalid JSON')
def paths(values):return sorted(set(c(item,120) for item in values[:30] if isinstance(values,list) and c(item,120))) if isinstance(values,list) else []

@allow_storage
@dataclass
class Review:
 owner:Address;service:str;revision:str;sources:str;authorities:str;release_controller:Address;snapshots:str;digests:str;attested:str;state:str;verdict:str;breaking:str;covered:str

class SchemaSentry(gl.Contract):
 reviews:TreeMap[str,Review]
 def __init__(self):pass
 def _get(self,review_id):
  key=ident(review_id)
  if key not in self.reviews:raise gl.vm.UserError(EXPECTED+' review not found')
  return key,self.reviews[key]
 def _freeze(self,urls):
  def run():
   snapshots=[];digests=[]
   for url in urls:
    response=gl.nondet.web.get(url)
    if response.status in (403,429) or response.status>=500:raise gl.vm.UserError(TRANSIENT+' source unavailable')
    if response.status!=200:raise gl.vm.UserError(EXTERNAL+' source unavailable')
    raw=response.body if isinstance(response.body,bytes) else str(response.body).encode();digests.append(hashlib.sha256(raw).hexdigest());snapshots.append(raw.decode(errors='replace')[:16000])
   return {'snapshots':snapshots,'digests':digests}
  def validate(leader):
   if not isinstance(leader,gl.vm.Return):return False
   try:mine=run();theirs=leader.calldata
   except gl.vm.UserError:return False
   return mine['snapshots']==theirs.get('snapshots') and mine['digests']==theirs.get('digests')
  return gl.vm.run_nondet_unsafe(run,validate)
 @gl.public.write
 def register(self,review_id:str,service:str,revision:str,sources:list[str],source_authorities:list[str],release_controller:str)->None:
  key=ident(review_id)
  if key in self.reviews:raise gl.vm.UserError(EXPECTED+' duplicate review id')
  parsed=[link(item) for item in sources];owner=gl.message.sender_address
  try:authorities=[Address(item) for item in source_authorities];controller=Address(release_controller)
  except:raise gl.vm.UserError(EXPECTED+' valid authority addresses required')
  if len(parsed)!=3 or len(set(item[1] for item in parsed))!=3:raise gl.vm.UserError(EXPECTED+' three independent source hosts required')
  if len(authorities)!=3 or len(set(item.as_hex.lower() for item in authorities))!=3 or any(item==owner for item in authorities):raise gl.vm.UserError(EXPECTED+' three independent source authorities required')
  if controller==owner:raise gl.vm.UserError(EXPECTED+' independent release controller required')
  frozen=self._freeze([item[0] for item in parsed])
  self.reviews[key]=Review(owner,c(service,120),c(revision,80),json.dumps([item[0] for item in parsed]),json.dumps([item.as_hex for item in authorities]),controller,json.dumps(frozen['snapshots']),json.dumps(frozen['digests']),json.dumps([False,False,False]),'PENDING_ATTESTATIONS','','[]','[]')
 @gl.public.write
 def attest_source(self,review_id:str,slot:u256,digest:str)->None:
  _,review=self._get(review_id);index=int(slot);authorities=[Address(item) for item in json.loads(review.authorities)];attested=json.loads(review.attested);digests=json.loads(review.digests)
  if review.state!='PENDING_ATTESTATIONS' or index<0 or index>=3 or gl.message.sender_address!=authorities[index] or c(digest,64).lower()!=digests[index]:raise gl.vm.UserError(EXPECTED+' matching source authority attestation required')
  if attested[index]:raise gl.vm.UserError(EXPECTED+' source already attested')
  attested[index]=True;review.attested=json.dumps(attested)
  if all(attested):review.state='READY'
 def _compare(self,review):
  docs=[{'slot':index,'digest':json.loads(review.digests)[index],'body':body} for index,body in enumerate(json.loads(review.snapshots))]
  def run():
   prompt='SchemaSentry. Compare frozen old OpenAPI slot 0 with frozen candidate slot 1 under frozen migration policy slot 2. JSON only {"verdict":"COMPATIBLE|MIGRATION_REQUIRED|BLOCKED|INSUFFICIENT","breaking_paths":[],"covered_paths":[]}. Exact paths only. SERVICE:'+review.service+' REVISION:'+review.revision+' DOCS:'+json.dumps(docs)
   data=obj(gl.nondet.exec_prompt(prompt,response_format='json'));verdict=c(data.get('verdict'),30).upper();breaking=paths(data.get('breaking_paths',[]));covered=paths(data.get('covered_paths',[]))
   if verdict not in VERDICTS:raise gl.vm.UserError(LLM+' invalid verdict')
   if verdict=='COMPATIBLE' and breaking:raise gl.vm.UserError(LLM+' compatible verdict cannot contain breaking paths')
   if verdict in ('MIGRATION_REQUIRED','BLOCKED') and not breaking:raise gl.vm.UserError(LLM+' blocking verdict must identify paths')
   return {'verdict':verdict,'breaking':breaking,'covered':covered}
  def validate(leader):
   if not isinstance(leader,gl.vm.Return):return False
   try:mine=run();theirs=leader.calldata
   except gl.vm.UserError:return False
   return mine['verdict']==theirs.get('verdict') and mine['breaking']==theirs.get('breaking') and mine['covered']==theirs.get('covered')
  return gl.vm.run_nondet_unsafe(run,validate)
 @gl.public.write
 def review(self,review_id:str)->None:
  _,review=self._get(review_id)
  if review.state!='READY':raise gl.vm.UserError(EXPECTED+' three attestations required')
  result=self._compare(review);review.verdict=result['verdict'];review.breaking=json.dumps(result['breaking']);review.covered=json.dumps(result['covered']);review.state='APPROVED' if result['verdict']=='COMPATIBLE' else 'BLOCKED'
 @gl.public.write
 def execute_release(self,review_id:str)->None:
  _,review=self._get(review_id)
  if review.state!='APPROVED' or review.verdict!='COMPATIBLE' or gl.message.sender_address!=review.release_controller:raise gl.vm.UserError(EXPECTED+' approved release controller required')
  review.state='RELEASED'
 @gl.public.view
 def get_review(self,review_id:str)->dict:
  key,review=self._get(review_id);return {'id':key,'owner':review.owner.as_hex,'service':review.service,'revision':review.revision,'sources':json.loads(review.sources),'sourceAuthorities':json.loads(review.authorities),'releaseController':review.release_controller.as_hex,'snapshots':json.loads(review.snapshots),'digests':json.loads(review.digests),'attested':json.loads(review.attested),'state':review.state,'verdict':review.verdict,'breakingPaths':json.loads(review.breaking),'coveredPaths':json.loads(review.covered)}
