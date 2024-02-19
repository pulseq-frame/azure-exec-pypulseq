import requests

seq = "epi"  # Provided examples: "gre", "tse", "epi"
seq_script = f"client_example/write_{seq}.py"

run_local = False
if run_local:
    url = "http://localhost:7071/api/httpscriptupload"
else:
    url = "https://azure-exec-pypulseq.azurewebsites.net/api/httpscriptupload"

response = requests.get(url, files={"seq_script": open(seq_script, "r")})

if response.status_code != 200:
    print(f"Error:\n{response.text}")
else:
    file_name = response.headers["Content-Disposition"].split('"')[1]
    path = f"client_example/{file_name}"
    with open(path, "w") as f:
        f.write(response.text)
    print(f"wrote {len(response.content)} bytes to {path}")
