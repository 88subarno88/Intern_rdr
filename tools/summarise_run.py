import sys,json
raw=open(sys.argv[1]).read(); i=raw.find('{\n')
try: d=json.loads(raw[i:])
except Exception as e: print('parse fail',e); print(raw[-2500:]); sys.exit()
rd=d['data']['resultData']
print('status',d.get('status'),'| last:',rd.get('lastNodeExecuted'),'| error:',json.dumps(rd.get('error'))[:500])
for name,runs in rd['runData'].items():
    r=runs[0]; out=r.get('data',{}).get('main',[[]]); n=len(out[0]) if out and out[0] else 0
    print(f"  {name:22s} items={n} {('ERR '+json.dumps(r['error'])[:300]) if r.get('error') else ''}")
for nm in sys.argv[2:]:
    if nm in rd['runData']:
        o=rd['runData'][nm][0].get('data',{}).get('main',[[]])[0]
        for it in o[:6]: print('   >',nm,json.dumps(it['json'])[:420])
