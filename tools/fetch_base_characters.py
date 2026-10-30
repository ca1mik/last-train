"""Use the author's public, zero-price 'No thanks, take me to downloads' flow."""
from pathlib import Path
from bs4 import BeautifulSoup
import requests, json, zipfile, hashlib

root=Path(__file__).resolve().parent.parent
session=requests.Session()
base='https://quaternius.itch.io/universal-base-characters'
page=session.get(base+'/purchase',timeout=25);page.raise_for_status()
soup=BeautifulSoup(page.text,'html.parser')
csrf=soup.select_one('input[name=csrf_token]')['value']
response=session.post(base+'/download_url',data={'csrf_token':csrf},headers={'Referer':base+'/purchase','Origin':'https://quaternius.itch.io','X-Requested-With':'XMLHttpRequest'},timeout=25)
response.raise_for_status();data=response.json()
if 'url' not in data:raise RuntimeError('Public free-download flow did not return a page')
download=session.get(data['url'],timeout=25);download.raise_for_status()
(root/'release/base-characters-download.html').write_text(download.text,encoding='utf-8')
doc=BeautifulSoup(download.text,'html.parser')
for upload in doc.select('.upload'):
    print(upload.get_text(' ',strip=True)[:250])
    if '[Standard]' not in upload.get_text():continue
    button=upload.select_one('.download_btn')
    item=session.post(base+'/file/'+button['data-upload_id'],params={'source':'game_download'},data={'csrf_token':csrf},headers={'Referer':data['url'],'Origin':'https://quaternius.itch.io','X-Requested-With':'XMLHttpRequest'},timeout=25)
    item.raise_for_status();info=item.json()
    if 'url' not in info:raise RuntimeError('Free standard download did not return a file; no access restriction bypassed')
    file=session.get(info['url'],stream=True,timeout=(25,60));file.raise_for_status()
    target=root/'source_25d/base-characters-standard.zip'
    with target.open('wb') as output:
        for chunk in file.iter_content(1048576):output.write(chunk)
    if not zipfile.is_zipfile(target):raise RuntimeError('Downloaded file is not a zip')
    destination=root/'source_25d/base-characters-standard';destination.mkdir(exist_ok=True)
    with zipfile.ZipFile(target) as archive:
        for member in archive.infolist():
            resolved=(destination/member.filename).resolve()
            if not resolved.is_relative_to(destination.resolve()):raise RuntimeError('Archive path escapes destination')
        archive.extractall(destination)
        print('FILES',archive.namelist())
    print('STANDARD_DOWNLOADED',target.stat().st_size,'SHA256',hashlib.sha256(target.read_bytes()).hexdigest())
