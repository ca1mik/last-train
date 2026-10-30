"""Fetch license notices from the exact pygame-ce source tag used by this build."""
import json
from pathlib import Path
import shutil
import sys
from urllib.request import Request, urlopen

root=Path(__file__).resolve().parent.parent/'release'/'licenses'
root.mkdir(parents=True,exist_ok=True)
headers={'User-Agent':'LastTrain-build-notices'}
def fetch(url):
    with urlopen(Request(url,headers=headers),timeout=30) as response:return response.read()
base='https://raw.githubusercontent.com/pygame-community/pygame-ce/2.5.8/'
(root/'pygame-ce-LGPL-2.1.txt').write_bytes(fetch(base+'docs/LGPL.txt'))
api='https://api.github.com/repos/pygame-community/pygame-ce/contents/docs/licenses?ref=2.5.8'
for entry in json.loads(fetch(api)):
    if entry['type']=='file':
        name=Path(entry['name']).name
        (root/('pygame-dependency-'+name)).write_bytes(fetch(entry['download_url']))
python_license=Path(sys.base_prefix)/'LICENSE.txt'
if python_license.exists():shutil.copy2(python_license,root/'Python-3.12-LICENSE.txt')
from importlib.metadata import distribution
for file in distribution('pyinstaller').files:
    if str(file).endswith('licenses/COPYING.txt'):
        shutil.copy2(distribution('pyinstaller').locate_file(file),root/'PyInstaller-COPYING.txt')
print('Collected',len(list(root.iterdir())),'license notice files')
