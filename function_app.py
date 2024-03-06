import azure.functions as func
import logging
import os
import builtins
import re

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

template = open("script_template.py", "br").read()


def delete_files(files):
    # We don't sanitize input - user code could call os.remove() itself anyways
    for file in files:
        try:
            os.remove(file)
            logging.info(f"deleted {file}")
        except FileNotFoundError:
            pass


def prep_script(source: bytes) -> bytes:
    # Un-escape if source is contained in a markdown code block
    codeblock = re.search(b"```python(.*?)```", source, re.DOTALL)
    if codeblock:
        total_len = len(source)
        source = codeblock.group(1)
        logging.info(f"Extracted markdown code block: ({len(source)} / {total_len}) characters")

    return template.replace(b"# INSERT USER SCRIPT HERE", source)


@app.route(route="HttpScriptUpload")
def HttpScriptUpload(req: func.HttpRequest) -> func.HttpResponse:
    # Prepare the environment the script runs in
    builtin_open = builtins.open
    seq_script = req.files.get("seq_script").read()
    logging.info(f"Recieved script ({len(seq_script)} bytes)")
    script_source = prep_script(seq_script)
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
        # the template has a fallback if seq.write is missing, we should always
        # have at least one .seq file! If not, there is a bug somewhere
        msg = "BUG: No .seq was written (not even fallback.seq)"
        logging.error(msg)
        return func.HttpResponse(msg, status_code=500)

    else:
        # NOTE: If there are multiple .seq files, we just silently return
        # the one that as created first. 
        name, path = next(iter(files.items()))
        logging.info(f"Returning to client: {name} from {path}")
        seq_file = open(path, "rb").read()

        delete_files(files.keys())
        
        # If the file is named 'fallback.seq' it is a sequence that the script
        # created but did not write to disk. If it's 'empty_fallback.seq', the
        # script did not create any sequence at all and we created a dummy.
        headers = {"Content-Disposition": f'attachment; filename="{name}"'}
        return func.HttpResponse(seq_file, headers=headers)
