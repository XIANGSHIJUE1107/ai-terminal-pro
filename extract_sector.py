import json

d = json.load(open(r'D:\营业部分析\sector_data.json', 'r', encoding='utf-8'))
compact = {}
for code, data in d.items():
    compact[code] = {
        'n': data.get('简称', ''),
        'p': data.get('现价', 0),
        'c': data.get('涨跌幅', 0),
        'a': data.get('成交额', 0),
        'ni': data.get('当日净流入额', 0),
        'nr': data.get('当日净流入率', 0),
        'ii': data.get('机构资金净流入', 0),
    }

sorted_items = sorted(compact.items(), key=lambda x: x[1]['ni'], reverse=True)
for i, (code, data) in enumerate(sorted_items[:20]):
    print(f"{i+1}. {data['n']}: inflow={data['ni']/1e8:.1f}亿, inst={data['ii']/1e8:.1f}亿, chg={data['c']}%")

print(f"\nTotal sectors: {len(compact)}")

with open(r'D:\营业部分析\sector_compact.json', 'w', encoding='utf-8') as f:
    json.dump(compact, f, ensure_ascii=False)
print('Saved sector_compact.json')