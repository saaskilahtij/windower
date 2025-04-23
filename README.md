```
     _     _     _   O             ___        __     _     _     _   ____
     \    | \    |  /|\  __    _  | ___\    /    \    \    | \    |  |   \
      \   |  \   |   |   | \   |  | ^ ^ \  / 0  0 \    \   |  \   |  |____\
       \  |   \  |   |   |  \  |  |   _ /  \   \  /     \  |   \  |  |   \
        \ |    \ |   |   |   \ |  | ___/    \ __ /       \ |    \ |  |    \
         \|     \|   |   |    \|  |___/      \__/         \|     \|  |     \
                         windows made quick and easy
options:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  Path to the JSON file
  -csv OUTPUT_CSV, --output-csv OUTPUT_CSV
                        Output file name
  -json OUTPUT_JSON, --output-json OUTPUT_JSON
                        Output file name
  -list, --list-ecus    List ECU names, can only be used with file and optional logging argument
  -e ECU [ECU ...], --ecu ECU [ECU ...]
                        Filter data by specific ECU name(s)
  -l LENGTH, --length LENGTH
                        Window length in seconds
  -s STEP, --step STEP  How many seconds the window moves forward (default: same as window length)
  -d, --debug           Enable DEBUG logging, default: INFO logging
  -q, --quiet           Show only ERRORs, default: INFO logging
```
