# -*- coding: utf-8 -*-
"""检查terminal.html语法"""
import re
with open('terminal.html','r',encoding='utf-8') as f:
    content=f.read()
opens = content.count('{')
closes = content.count('}')
parens_o = content.count('(')
parens_c = content.count(')')
brackets_o = content.count('[')
brackets_c = content.count(']')
print(f'{{ }} : {opens} / {closes} (diff={opens-closes})')
print(f'( ) : {parens_o} / {parens_c} (diff={parens_o-parens_c})')
print(f'[ ] : {brackets_o} / {brackets_c} (diff={brackets_o-brackets_c})')
scripts = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
print(f'Script blocks: {len(scripts)}')
for i,s in enumerate(scripts):
    lines = s.strip().split('\n')
    first = lines[0][:100] if lines else 'empty'
    print(f'  Script {i+1}: {len(lines)} lines -> {first}')
