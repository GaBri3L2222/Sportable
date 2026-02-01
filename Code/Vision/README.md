## Prerequisites

* Python3 (https://www.python.org/downloads/)
* Ingescape python binding (from pip)

## Install dependencies
A requirements.txt is provided. Install dependencies using pip
```bash
pip install -r requirements.txt
```


## Run
You can pass arguments to the main script to configure your agent.
```bash
<<<<<<< HEAD
python3 src/main.py --device en0 --port 5670 --name "Vision"
```

On windows you can use :
```bash
python main.py --verbose --port 5670 --device "Wi-Fi" --name Vision
=======
python3 src/main.py --device en0 --port 5670 --name "MyAgent"
>>>>>>> e5a0e1401f983429f320a6a07591bbcf59c601ff
```
Some parameters are optional, others are mandatory. Use `--help` to learn more.



