"""Start real pinned ComfyUI on CPU and exercise plugin routes without models."""
from pathlib import Path
import json,os,shutil,subprocess,sys,time,urllib.request,zipfile
root=Path(__file__).resolve().parents[1]
comfy=root/'.comfy'
with zipfile.ZipFile(root/'dist'/f'{root.name}.zip') as z:z.extractall(comfy/'custom_nodes')
env=os.environ.copy();env['MRG_DATABASE']=str(comfy/'db'/'mrg.db')
env['MRG_COMFY_ADDRESS']='127.0.0.1:18188'
log=root/'comfy-smoke.log'
with log.open('w') as stream:
    process=subprocess.Popen([sys.executable,'main.py','--cpu','--listen','127.0.0.1','--port','18188','--front-end-root',str(root/'.frontend'),'--disable-auto-launch'],cwd=comfy,env=env,stdout=stream,stderr=subprocess.STDOUT)
    try:
        for attempt in range(120):
            if process.poll() is not None:raise RuntimeError('ComfyUI stopped during startup')
            try:
                with urllib.request.urlopen('http://127.0.0.1:18188/mrg/categories_tree',timeout=2) as response:
                    data=json.load(response)
                    assert data
                break
            except OSError:time.sleep(1)
        else:raise RuntimeError('Plugin route did not become ready')
        for route in ['mrg/default.htm','mrg/bundle']:
            with urllib.request.urlopen('http://127.0.0.1:18188/'+route,timeout=30) as response:
                assert response.status==200 and response.read()
        subprocess.run(['node','--check',str(root/'.frontend/mrg/app/bundle.js')],check=True)
        print('Real ComfyUI CPU startup, database API, web page and JavaScript bundle passed')
    finally:
        process.terminate()
        try:process.wait(timeout=10)
        except subprocess.TimeoutExpired:process.kill();process.wait()
        print(log.read_text(errors='replace'))
