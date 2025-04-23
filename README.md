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
  -b, --buffered        Enable buffered writing for output files
  --buffer-size BUFFER_SIZE
                        Number of entries to buffer before flushing (default: 1000)
  -w, --watch           Watch for updates to the input file and process them as they come in
  --watch-interval WATCH_INTERVAL
                        Interval in seconds to check for file updates (default: 1.0)
  -d, --debug           Enable DEBUG logging, default: INFO logging
  -q, --quiet           Show only ERRORs, default: INFO logging
```
