"""Record artifact identity. This is not a declaration of release readiness."""
from pathlib import Path
import hashlib
import json
import sys
from datetime import datetime, timezone

root=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(root))
from lasttrain import __version__
version='.'.join(__version__.split('.')[:2])
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
source=[root/'main.py',root/'LastTrain.spec',root/'requirements.txt']
source+=sorted((root/'lasttrain').rglob('*.py'))
source+=sorted((root/'assets').rglob('*.png'))
source+=sorted((root/'assets').rglob('*.json'))
source+=sorted((root/'assets').rglob('*.ogg'))
source+=sorted((root/'assets'/'audio').rglob('*.txt'))
exe=root/'dist'/('LastTrain-'+version)/'LastTrain.exe'
data={'version':__version__,'release_ready':False,
      'recorded_utc':datetime.now(timezone.utc).isoformat(),
      'exe':str(exe.relative_to(root)).replace('\\','/'),
      'exe_sha256':digest(exe),
      'source_sha256':{str(p.relative_to(root)).replace('\\','/'):digest(p) for p in source}}
(root/'release'/('build-'+version+'.json')).write_text(json.dumps(data,indent=2),encoding='utf-8')
print('Recorded development build manifest')
