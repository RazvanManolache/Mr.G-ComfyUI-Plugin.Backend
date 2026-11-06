from pathlib import Path
import ast,importlib.util,os,tempfile,subprocess
root=Path(__file__).resolve().parents[1]
for path in root.glob('*.py'):
    compile(path.read_text(encoding='utf-8-sig'),str(path),'exec')
def module(name):
    spec=importlib.util.spec_from_file_location(name,root/(name+'.py'))
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
with tempfile.TemporaryDirectory() as directory:
    path=Path(directory)
    os.environ['MRG_DATABASE']=str(path/'new'/'mrg.db')
    db=module('mrg_database')
    assert db.database.table_exists('categories')
    assert len(list(db.get_categories()))==3
    db.database.close()
    bundle=module('mrg_bundle')
    (path/'BaseC.js').write_text('const base = 1;')
    (path/'application.js').write_text('console.log(base);')
    output=bundle.bundle_javascript_files(path,'bundle.js')
    first=output.read_bytes()
    assert first.index(b'const base') < first.index(b'console.log')
    assert bundle.bundle_javascript_files(path,'bundle.js').read_bytes()==first
print('Python syntax, fresh database initialization and repeatable first-run bundling passed')
