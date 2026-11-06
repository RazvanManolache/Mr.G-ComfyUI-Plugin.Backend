import os
import glob


bundle_files_order = [
    "BaseC.js",
    "BaseVM",
    "BaseModel",
    "SimpleModel",
    "SelectListModel",
    "WorkflowExtenderModel",
    "BaseMemoryStore",
    "SimpleStore",    
    "BaseContainerVM",
    "BaseContainerC",
    "BaseContainerV.js",
    "BasePanelVM",
    "BasePanelC",
    "BasePanelV.js",
    "BaseNodePanelVM",
    "BaseNodePanelC",
    "BaseNodePanelV.js",
   
    
    "BaseFieldVM",
    "BaseFieldC",
    "BaseFieldV.js",

    'NumberCombo',
	'NumberDefinedSequence',
	'NumberMinMax.js',
	'NumberMinMaxAdvanced',
	'NumberMinMaxSummary',
	'NumberSequence',
	'NumberSimple',
	'NumberWithDefinedSequenceAdvanced',
	'NumberWithDefinedSequenceSummary',
    'NumberC.js',
    'NumberVM',	
    'NumberV.js',

    'TextC',
    'TextVM',
    'TextV.js',
	
	'BoolC',
    'BoolVM',	
    'BoolV.js',
    'SelectionC',
    'SelectionVM',	
    'SelectionV.js',
    'ImageC',
    'ImageVM',
    'ImageV.js',
    
	"BaseNodeVM",
    "BaseNodeC",
    "BaseNodeV.js",
   
    "WorkflowVM",
    "WorkflowC",
    "WorkflowV.js",
    
]

end_files = ["application.js"]

def bundle_javascript_files(directory, output_file):
    from pathlib import Path
    directory = Path(directory).resolve()
    output = directory / output_file
    files = sorted(path for path in directory.rglob("*.js") if path != output)
    if not files:
        raise FileNotFoundError(f"No application scripts in {directory}")
    ordered = []
    for name in bundle_files_order:
        matches = [path for path in files if name in path.name and path.name not in end_files]
        ordered.extend(matches)
        files = [path for path in files if path not in matches]
    ordered.extend(path for path in files if path.name not in end_files and path.name.endswith(("VM.js", "C.js")))
    ordered.extend(path for path in files if path not in ordered and path.name not in end_files)
    ordered.extend(path for path in files if path.name in end_files)
    output.write_text("\n;\n".join(path.read_text(encoding="utf-8-sig") for path in ordered) + "\n", encoding="utf-8")
    return output
