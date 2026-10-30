"""Inventory authored content. Branch totals are never a playtime claim."""
import json
import re
import sys
from pathlib import Path
root=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(root))
from lasttrain import __version__
from lasttrain.content import DIALOGUES,SCENES

def inventory():
    chapters={str(i):{'dialogues':0,'lines':0,'words_all_branches':0,'choice_points':0} for i in range(1,6)}
    unique_lines=set()
    for key,data in DIALOGUES.items():
        match=re.match(r'c([2-5])_',key)
        chapter=chapters[match[1] if match else '1']
        chapter['dialogues']+=1;chapter['lines']+=len(data['lines'])
        chapter['words_all_branches']+=sum(len(re.findall(r'\w+',line[1])) for line in data['lines'])
        chapter['choice_points']+=bool(data.get('choices'))
        unique_lines.update(re.sub(r'\s+',' ',line[1]).strip() for line in data['lines'])
    return {'version':__version__,'scenes':len(SCENES),'chapters':chapters,
            'words_all_branches':sum(c['words_all_branches'] for c in chapters.values()),
            'words_deduplicated_lines':sum(len(re.findall(r'\w+',line)) for line in unique_lines),
            'deduplication_scope':'Exact line text; still includes alternative routes, never a playtime estimate.',
            'scope':'All alternative and optional dialogue lines; not a single route or measured human playthrough.',
            'measured_human_duration_seconds':None,'several_hours_verified':False}

if __name__=='__main__':
    path=root/'release'/('story-audit-'+'.'.join(__version__.split('.')[:2])+'.json')
    path.write_text(json.dumps(inventory(),ensure_ascii=False,indent=2),encoding='utf-8')
    print(path)
