import azure.functions as func
import logging
import os
import builtins
import re

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

prelude = open("script_prelude.py", "r").read()


def delete_files(files):
    # We don't sanitize input - user code could call os.remove() itself anyways
    for file in files:
        try:
            os.remove(file)
            logging.info(f"deleted {file}")
        except FileNotFoundError:
            pass


def prep_script(source: str) -> str:
    # Un-escape if source is contained in a markdown code block
    codeblock = re.search("```python(.*?)```", source, re.DOTALL)
    if codeblock:
        total_len = len(source)
        source = codeblock.group(1)
        logging.info(f"Extracted markdown code block: ({len(source)} / {total_len}) characters")
    
    # Add a seq.write if not contained in the code
    if not re.search("seq.write\\(.*?\\)", source, re.DOTALL):
        source += "\n# ! Added by azure-exec-pypulseq\nseq.write('external.seq')\n"
        logging.info("Attached a seq.write(), as source did not contain one")

    return prelude + source


@app.route(route="HttpScriptUpload")
def HttpScriptUpload(req: func.HttpRequest) -> func.HttpResponse:
    # Prepare the environment the script runs in
    builtin_open = builtins.open
    script_source = prep_script(req.files.get("seq_script").read())
    script_globals = {
        "__name__": "__main__",
        "__loader__": globals()["__loader__"],
        "__builtins__": globals()["__builtins__"].copy(),
    }
    logging.warn("Executing script")
    try:
        exec(script_source, script_globals)
    except Exception as e:
        logging.error(e)
        return func.HttpResponse(str(e), status_code=500)

    # Restore the open function and get the files created by the script
    builtins.open = builtin_open
    files = script_globals.get("files", {})

    if len(files) == 0:
        msg = "Uploaded .py script did not write any .seq files"
        logging.error(msg)
        return func.HttpResponse(msg, status_code=400)

    elif len(files) > 1:
        msg = f"Uploaded .py script wrote more than one .seq file: {files.keys()}"
        logging.error(msg)
        delete_files(files.keys())
        return func.HttpResponse(msg, status_code=400)

    else:
        name, path = files.popitem()
        logging.info(f"Returning to client: {name} from {path}")
        seq_file = open(path, "rb").read()

        delete_files([path])

        headers = {"Content-Disposition": f'attachment; filename="{name}"'}
        return func.HttpResponse(seq_file, headers=headers)
