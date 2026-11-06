# GitHub package

Open **Actions > Plugin package and ComfyUI checks > Run workflow**. Download the
successful run's **ComfyUI-Backend-plugin** artifact and extract the ZIP inside it
into `ComfyUI/custom_nodes`. Install `requirements.txt` with ComfyUI's Python.
Install the separate Mr.G Web plugin into your active web root's `mrg` directory.
Start ComfyUI, then open `http://127.0.0.1:8188/mrg/default.htm`.

The workflow checks a fresh database, repeatable JavaScript bundling and real CPU
startup/API requests against Mr.G-ComfyUI commit
`96f117e9abf9830d3efdc32604581ff67b205858`. Other upstream revisions and GPU image
generation are not covered. The plugin is intended for that legacy fork.

The default database remains `db/mrg.db` under the ComfyUI working directory.
Its folder is created automatically. Set `MRG_DATABASE` to choose another path.
Set `MRG_COMFY_ADDRESS` if ComfyUI uses a host/port other than `127.0.0.1:8188`.
Database files, caches and the test ComfyUI installation are excluded from downloads.
