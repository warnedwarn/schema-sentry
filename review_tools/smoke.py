import json, re, time
from pathlib import Path
from genlayer_py import create_client, create_account
from genlayer_py.chains import studionet
from genlayer_py.types import TransactionStatus

ROOT = Path(__file__).parents[1]
ENV = (ROOT.parents[3] / "accounts.env").read_text()
DEPLOYMENT = json.loads((ROOT / "evidence/deployment.json").read_text())

def value(name):
    return re.search(rf'^{name}\s*=\s*"?([^"\r\n]+)', ENV, re.M).group(1).strip()

accounts = [create_account(account_private_key=value(f"ACCOUNT_{index}_GENLAYER_PRIVATE_KEY")) for index in (2, 1, 3, 4)]
clients = [create_client(chain=studionet, account=account) for account in accounts]
contract = DEPLOYMENT["contract"]
commit = DEPLOYMENT["sourceCommit"]
review_id = f"SS-{int(time.time())}"
sources = [
    f"https://raw.githubusercontent.com/warnedwarn/schema-sentry/{commit}/evidence/old-api.txt",
    f"https://cdn.jsdelivr.net/gh/warnedwarn/schema-sentry@{commit}/evidence/new-api.txt",
    f"https://github.com/warnedwarn/schema-sentry/raw/{commit}/evidence/migration-policy.txt",
]

def send(client, name, args):
    tx = client.write_contract(address=contract, function_name=name, args=args)
    print(name, tx, flush=True)
    client.wait_for_transaction_receipt(transaction_hash=tx, status=TransactionStatus.ACCEPTED, retries=120, interval=10000)
    info = client.get_transaction(transaction_hash=tx)
    if info.get("status_name") != "ACCEPTED" or info.get("tx_execution_result_name") not in ("SUCCESS", None):
        raise RuntimeError(info)
    return tx

transactions = {}
transactions["register"] = send(clients[0], "register", [review_id, "Profiles API", "v2", sources, [account.address for account in accounts[1:]], accounts[3].address])
state = clients[0].read_contract(address=contract, function_name="get_review", args=[review_id])
for slot in range(3):
    transactions[f"attest{slot}"] = send(clients[slot + 1], "attest_source", [review_id, slot, state["digests"][slot]])
transactions["review"] = send(clients[0], "review", [review_id])
transactions["executeRelease"] = send(clients[3], "execute_release", [review_id])
state = clients[0].read_contract(address=contract, function_name="get_review", args=[review_id])
if state["state"] != "RELEASED" or state["verdict"] != "COMPATIBLE" or not all(state["attested"]):
    raise RuntimeError(state)
(ROOT / "evidence/network-run.json").write_text(json.dumps({"id": review_id, "contract": contract, "sourceCommit": commit, "transactions": transactions, "state": state}, indent=2))
print(json.dumps(state, indent=2), flush=True)
