import os
import glob

from _pytest.stash import D

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
    # Get all JavaScript files in the directory
    absolute_directory = os.getcwd()+directory

    js_files = glob.glob(os.path.join(absolute_directory, "**/*.js"), recursive=True)

    files = []
    for js_file in js_files:
        files.append(js_file)
     
    for file in files:
        if "bundle.js" in file:
            files.remove(file)
    files_end = []
    

    temp_files = files.copy()
    for file in temp_files:
        for end_file in end_files:
            if end_file in file:
                files_end.append(file)
                files.remove(file)

    files_sorted = []
       
    temp_files = files.copy()
    for name in bundle_files_order:
        for js_file in temp_files:
            if name in js_file:
                
                files_sorted.append(js_file)
                files.remove(js_file)
    
    #sort files so that files ending with VM.js and C.js are first and ones ending in 'V.js' are last
    struct_files = []
    temp_files = files.copy()
    for file in temp_files:
        if file.endswith("VM.js") or file.endswith("C.js"):
            struct_files.append(file)
            files.remove(file)
            
    for file in struct_files:
        files_sorted.append(file)
        
    for file in files:
        files_sorted.append(file)
        
    for end_file in files_end:
        files_sorted.append(end_file)
        
    os.remove(absolute_directory+output_file)
    # Create the output file
    with open(absolute_directory+output_file, "w") as outfile:
        # Iterate through each JavaScript file
        for js_file in files_sorted:
            # Read the contents of the JavaScript file
            with open(js_file, "r") as infile:
                # Write the contents to the output file
                outfile.write(infile.read())
                outfile.write("\n")


