# Diigo export
Diigo's bookmark export functionality appears to have been broken for a long time.
This is a script to export its boomarks to a CSV that can then be imported into e.g. Raindrop.io.

## Steps

- Generate a Diigo API key [here](https://diigo.com/api_keys);
- Set an environment variable `DIIGO_API_KEY` with its value;
- Run `pip install -r requirements.txt`;
- Call `python export.py`, passing your Diigo username & password when prompted
  (unfortunately, only HTTP Basic Auth is supported by the Diigo API);
- Import the generated `diigo_export.csv` to a different website e.g. Raindrops.io
