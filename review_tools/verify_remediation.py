import base64,json,re
from pathlib import Path
from genlayer_py import create_client,create_account
from genlayer_py.chains import studionet

ROOT=Path(__file__).parents[1]
deployment=json.loads((ROOT/'evidence'/'deployment.json').read_text())
run=json.loads((ROOT/'evidence'/'network-run.json').read_text())
env=(ROOT.parents[3]/'accounts.env').read_text()
key=re.search(r'^ACCOUNT_2_GENLAYER_PRIVATE_KEY\s*=\s*"?([^"\r\n]+)',env,re.M).group(1).strip()
account=create_account(account_private_key=key)
client=create_client(chain=studionet,account=account)

txs={'deployment':deployment['deploymentTx'],**run['transactions']}
records={name:client.get_transaction(transaction_hash=tx) for name,tx in txs.items()}
def execution(record):
 rows=(record.get('consensus_data') or {}).get('leader_receipt') or []
 return rows[0].get('execution_result') if rows else None

deployed=base64.b64decode(records['deployment']['data']['contract_code']).decode()
local=(ROOT/'sentry_core'/'schema_sentry.py').read_text()
state=client.read_contract(address=deployment['contract'],function_name='get_review',args=[run['id']])
out={'contract':deployment['contract'],'wallet':account.address,'sourceMatches':deployed==local,'reviewId':run['id'],'state':state['state'],'verdict':state['verdict'],'attested':state['attested'],'transactions':{name:{'hash':txs[name],'status':record.get('status_name'),'consensus':record.get('result_name'),'execution':execution(record)} for name,record in records.items()}}
assert out['sourceMatches'] and account.address.lower()==deployment['deployer'].lower()
assert state['state']=='RELEASED' and state['verdict']=='COMPATIBLE' and all(state['attested'])
assert all(item['status']=='FINALIZED' and item['consensus']=='MAJORITY_AGREE' and item['execution']=='SUCCESS' for item in out['transactions'].values())
(ROOT/'evidence'/'remediation-verification.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
