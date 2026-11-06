"""Package only tracked runtime files, with build identity and per-file hashes."""
from pathlib import Path
import hashlib,json,subprocess,zipfile
ROOT=Path(__file__).resolve().parents[1]
NAME=ROOT.name
TRACKED=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
FILES=[]
for name in sorted(filter(None,TRACKED)):
    p=Path(name)
    if p.parts[0] in {'.github','tools','tests','junk'} or p.name.startswith('.'):continue
    if p.suffix in {'.pyc','.db','.bec'}:continue
    FILES.append(name)
assert FILES, 'No runtime files selected'
SHA=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
manifest={'repository':NAME,'commit':SHA,'files':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in FILES}}
out=ROOT/'dist';out.mkdir(exist_ok=True)
archive=out/(NAME+'.zip')
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for name in FILES:z.write(ROOT/name,NAME+'/'+name)
    z.writestr(NAME+'/BUILDINFO.json',json.dumps(manifest,indent=2)+'\n')
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for name,digest in manifest['files'].items():assert hashlib.sha256(z.read(NAME+'/'+name)).hexdigest()==digest
(out/'SHA256SUMS.txt').write_text(hashlib.sha256(archive.read_bytes()).hexdigest()+'  '+archive.name+'\n')
print(f'Packaged and verified {len(FILES)} files: {archive.name}')
