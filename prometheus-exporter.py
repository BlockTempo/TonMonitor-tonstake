#!/usr/bin/env python3

import subprocess
from prometheus_client import start_http_server, Gauge, Info
import time
import json

# Create a Gauge metric
gauge_metric = Gauge('validator_ls_sync', 'Time to last block of LS')
# Function to run the external Python script and get its output
def run_external_script():
    while True:
        # Replace 'your_script.py' with the name of your Python script
        cmd = ["python3", "scripts/check_ls_sync.py", "-c", "etc/config_local.json", "-a", "127.0.0.1:7777", "-b", "asdasda"]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode == 0:
            # Set the metric value to the output of the script
            gauge_metric.set(float(result.stdout))
        else:
            # Handle any errors here, for example, log them
            print(f"Script failed with error: {result.returncode}")
        
        time.sleep(5)

cycle_max_metric = Gauge('validator_cycle_max', 'Election cycle max staker')
def run_cycle_max_metric ():
    while True:
        # Replace 'your_script.py' with the name of your Python script
        cmd = ["python3", 'scripts/get_cycle_stats.py', '-c', 'etc/config.json', '--metric', 'stake', '--info', 'max']
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode == 0:
            # Set the metric value to the output of the script
            cycle_max_metric.set(float(result.stdout))
        else:
            # Handle any errors here, for example, log them
            print(f"Script failed with error: {result.returncode}")
        
        time.sleep(5)

election_participation_metric = Gauge('validator_election_participation', 'Election participation')
def run_election_participation_metric():
    while True:
        cmd = ["python3", "scripts/check_election_participation.py", "-c", "etc/config_local.json", adnlAddr]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode == 0:
            # Set the metric value to the output of the script
            election_participation_metric.set(float(result.stdout))
        else:
            # Handle any errors here, for example, log them
            print(f"Script failed with error: {result.returncode}")
        
        time.sleep(5)

adnl_address = Info('validator_adnl_address', 'only get once at the start of exporter')
def get_adnl_address():
    with open("/home/allenchan/.local/share/mytoncore/mytoncore.db", 'r') as f:
        data = json.load(f)
    adnlAddr = data.get('adnlAddr', None)

    if adnlAddr is not None:
        # Set the Info metric to the adnlAddr
        adnl_address.info({'adnlAddr': adnlAddr})
    else:
        # Handle any errors here, for example, log them
        print(f"Script failed with error: adnlAddr not found in JSON")

if __name__ == '__main__':
    # Start an HTTP server to expose the metrics
    start_http_server(8888)
    
    get_adnl_address()
    # Update the metric in the background by running the external script
    run_external_script()
    run_cycle_max_metric()
    run_election_participation_metric()
