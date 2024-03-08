import azure.functions as func
import logging
import os
import builtins
import re
import sys
import traceback
import json
from time import time

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

template = open("script_template.py", "r").read()
prelude_len = template.splitlines().index("# INSERT USER SCRIPT HERE")


# TODO: there are a couple more potential exceptions, like when no script file was sent;
# these should be handled and an appropriate HTML error code returned instead of crashing the app


def delete_files(files):
    # We don't need to sanitize input - user code could delete directly anyways
    for file in files:
        try:
            os.remove(file)
            logging.info(f"deleted {file}")
        except FileNotFoundError:
            pass


def prep_script(source):
    # Un-escape if source is contained in a markdown code block
    codeblock = re.search("```python(.*?)```", source, re.DOTALL)
    if codeblock:
        total_len = len(source)
        source = codeblock.group(1)
        logging.info("Extracted markdown code block: "
                     f"({len(source)} / {total_len}) characters")

    return template.replace("# INSERT USER SCRIPT HERE", source)


def get_exec_exc_lines():
    tb = traceback.extract_tb(sys.exc_info()[2])
    origin = tb[-1].line

    for frame in reversed(tb):
        if frame.filename == "<string>":
            return (frame.lineno, frame.end_lineno, origin)
    return (1, 1, origin)


@app.route(route="HttpScriptUpload")
def HttpScriptUpload(req: func.HttpRequest) -> func.HttpResponse:
    # Prepare the environment the script runs in
    builtin_open = builtins.open
    seq_script = req.files.get("seq_script").read().decode("utf-8")
    logging.info(f"Recieved script ({len(seq_script)} bytes)")

    script_source = prep_script(seq_script)
    script_globals = {
        "__name__": "__main__",
        "__loader__": globals()["__loader__"],
        "__builtins__": globals()["__builtins__"].copy(),
    }
    logging.info("Executing script")
    try:
        start = time()
        exec(script_source, script_globals)
        logging.info(f"Execution successful, took {time() - start} s")

    except SyntaxError as e:
        err = {
            "error": "SyntaxError",
            "msg": e.msg,
            "lineno": e.lineno - prelude_len,
            "line": e.text,
            "origin": ""
        }
        logging.error(err)
        return func.HttpResponse(json.dumps(err), status_code=400)

    except Exception as e:
        lineno, end_lineno, origin = get_exec_exc_lines()
        lines = script_source.splitlines()
        line = "".join(line.strip() for line in lines[lineno - 1:end_lineno])
        err = {
            "error": type(e).__name__,
            "msg": str(e),
            "lineno": lineno - prelude_len,
            "line": line,
            "origin": origin
        }
        logging.error(err)
        return func.HttpResponse(json.dumps(err), status_code=400)

    # Restore the open function and get the files created by the script
    builtins.open = builtin_open
    files = script_globals.get("files", {})
    if len(files) > 1:
        logging.warn(f"Script wrote multiple .seq files: {files.keys()}")

    # NOTE: The script template ensures there is at least one .seq file
    # If there are multiple, we return the first (and warn about it)
    name, path = next(iter(files.items()))
    logging.info(f"Returning to client: {name} from {path}")
    seq_file = open(path, "r").read()

    delete_files(files.keys())

    # If the file is named 'fallback.seq' it is a sequence that the script
    # created but did not write to disk. If it's 'empty_fallback.seq', the
    # script did not create any sequence at all and we created a dummy.
    headers = {"Content-Disposition": f'attachment; filename="{name}"'}
    return func.HttpResponse(seq_file, headers=headers)
