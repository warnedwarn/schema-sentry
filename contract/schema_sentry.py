# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
from dataclasses import dataclass
import hashlib,json
def c(v,n=1000):return str(v).strip()[:n]
def ident(v):
 k=c(v,72).upper()
 if not k:raise gl.vm.UserError('[EXPECTED] review id required')
 return k
def link(v):
 s=c(v,500);r=s[8:] if s.startswith('https://') else '';h=r.split('/')[0].lower();p=r[len(h):]
 if not h or '.' not in h or '@' in h or not p.startswith('/'):raise gl.vm.UserError('[EXPECTED] valid HTTPS source')
 return s,h
def obj(v):
 if isinstance(v,dict):return v
 s=str(v);a=s.find('{');b=s.rfind('}')
 if a<0 or b<=a:raise gl.vm.UserError('[LLM_ERROR] invalid JSON')
 return json.loads(s[a:b+1])
@allow_storage
@dataclass
class Review:owner:Address;service:str;revision:str;sources:str;state:str;verdict:str;breaking:str;covered:str;digests:str
class SchemaSentry(gl.Contract):
 reviews:TreeMap[str,Review]
 def __init__(self):pass
 def _get(self,i):
  k=ident(i)
  if k not in self.reviews:raise gl.vm.UserError('[EXPECTED] review not found')
  return k,self.reviews[k]
 def _compare(self,r):
  urls=json.loads(r.sources)
  def run():
   docs=[];dig=[]
   for ix,u in enumerate(urls):
    raw=gl.nondet.web.get(u).body[:16000];b=raw if isinstance(raw,bytes) else str(raw).encode();dig.append(hashlib.sha256(b).hexdigest());docs.append({'slot':ix,'body':b.decode(errors='replace')})
   q='Compare old OpenAPI slot 0 with new slot 1 under migration policy slot 2. Return JSON only {"verdict":"COMPATIBLE|MIGRATION_REQUIRED|BLOCKED|INSUFFICIENT","breaking_paths":[],"covered_paths":[]}. Every path must be an exact API path. SERVICE:'+r.service+' DOCS:'+json.dumps(docs)
   x=obj(gl.nondet.exec_prompt(q,response_format='json'));v=c(x.get('verdict'),30).upper();valid=('COMPATIBLE','MIGRATION_REQUIRED','BLOCKED','INSUFFICIENT')
   if v not in valid:v='INSUFFICIENT'
   return {'verdict':v,'breaking':sorted(set(c(x,120) for x in x.get('breaking_paths',[])[:30] if c(x,120))),'covered':sorted(set(c(x,120) for x in x.get('covered_paths',[])[:30] if c(x,120))),'digests':dig}
  def valid(x):
   if not isinstance(x,gl.vm.Return):return False
   try:
    g=x.calldata;docs=[];dig=[]
    for ix,u in enumerate(urls):
     raw=gl.nondet.web.get(u).body[:16000];b=raw if isinstance(raw,bytes) else str(raw).encode();dig.append(hashlib.sha256(b).hexdigest());docs.append({'slot':ix,'body':b.decode(errors='replace')})
    if g['digests']!=dig or g['verdict'] not in ('COMPATIBLE','MIGRATION_REQUIRED','BLOCKED','INSUFFICIENT'):return False
    q='Verify the exact verdict, breaking paths and covered paths from all three documents. JSON only {"valid":true}. PROPOSAL:'+json.dumps(g)+' DOCS:'+json.dumps(docs)
    return bool(obj(gl.nondet.exec_prompt(q,response_format='json')).get('valid',False))
   except:return False
  return gl.vm.run_nondet_unsafe(run,valid)
 @gl.public.write
 def register(self,i:str,service:str,revision:str,sources:list[str])->None:
  k=ident(i)
  if k in self.reviews:raise gl.vm.UserError('[EXPECTED] duplicate review id')
  p=[link(x) for x in sources]
  if len(p)!=3 or len(set(x[1] for x in p))!=3:raise gl.vm.UserError('[EXPECTED] three independent source hosts required')
  self.reviews[k]=Review(gl.message.sender_address,c(service,120),c(revision,80),json.dumps([x[0] for x in p]),'REGISTERED','','[]','[]','[]')
 @gl.public.write
 def review(self,i:str)->None:
  _,r=self._get(i)
  if r.state!='REGISTERED':raise gl.vm.UserError('[EXPECTED] review unavailable')
  x=self._compare(r);r.verdict=x['verdict'];r.breaking=json.dumps(x['breaking']);r.covered=json.dumps(x['covered']);r.digests=json.dumps(x['digests']);r.state='REVIEWED'
 @gl.public.write
 def acknowledge(self,i:str)->None:
  _,r=self._get(i)
  if r.owner!=gl.message.sender_address or r.state!='REVIEWED':raise gl.vm.UserError('[EXPECTED] owner reviewed record required')
  r.state='ACKNOWLEDGED'
 @gl.public.view
 def get_review(self,i:str)->dict:
  k,r=self._get(i);return {'id':k,'owner':r.owner.as_hex,'service':r.service,'revision':r.revision,'sources':json.loads(r.sources),'state':r.state,'verdict':r.verdict,'breakingPaths':json.loads(r.breaking),'coveredPaths':json.loads(r.covered),'digests':json.loads(r.digests)}
