from pathlib import Path

ROOT=Path(__file__).parents[1]
PAGE=(ROOT/'docs'/'compat-terminal.js').read_text()

def test_browser_registers_with_the_revised_signature():
 assert "'register',[value('id'),value('service'),value('rev'),[0,1,2].map(i=>value('source'+i)),[0,1,2].map(i=>value('authority'+i)),value('controller')]" in PAGE

def test_browser_exposes_every_revised_lifecycle_method():
 assert "'attest_source',[value('id'),BigInt(value('slot')),value('digest')]" in PAGE
 assert "'review',[value('id')]" in PAGE
 assert "'execute_release',[value('id')]" in PAGE
 assert "functionName:'get_review',args:[id]" in PAGE
 assert "'acknowledge'" not in PAGE

def test_browser_requires_final_validator_agreement():
 assert "status:'FINALIZED'" in PAGE
 assert "consensus!=='MAJORITY_AGREE'" in PAGE
 assert "FINALIZED / MAJORITY_AGREE / SUCCESS" in PAGE

def test_browser_uses_the_submitted_contract():
 deployment=__import__('json').loads((ROOT/'evidence'/'deployment.json').read_text())
 assert deployment['contract'] in PAGE
