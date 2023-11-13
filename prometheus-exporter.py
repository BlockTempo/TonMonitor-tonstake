#!/usr/bin/env python3

import subprocess
from prometheus_client import start_http_server, Gauge, Info
import time
import json
import requests
import asyncio
import aiohttp

# Create a Gauge metric
gauge_metric = Gauge('validator_ls_sync', 'Time to last block of LS')
# Function to run the external Python script and get its output
async def run_external_script():
    while True:
        # Replace 'your_script.py' with the name of your Python script
        cmd = ["python3", "scripts/check_ls_sync.py", "-c", "etc/config.json", "-a", "127.0.0.1:7777", "-b", "asdasda"]
        result = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await result.communicate()        

        if result.returncode == 0:
            # Set the metric value to the output of the script
            gauge_metric.set(float(stdout.decode().strip()))
        else:
            # Handle any errors here, for example, log them
            print(f"Script failed with error: {result.returncode}")
        
        await asyncio.sleep(5)

cycle_max_metric = Gauge('validator_cycle_max', 'Election cycle max staker')
async def run_cycle_max_metric ():
    while True:
        # Replace 'your_script.py' with the name of your Python script
        cmd = ["python3", 'scripts/get_cycle_stats.py', '-c', 'etc/config.json', '--metric', 'stake', '--info', 'max']
        result = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await result.communicate()
        
        if result.returncode == 0:
            # Set the metric value to the output of the script
            cycle_max_metric.set(float(stdout.decode().strip()))
        else:
            # Handle any errors here, for example, log them
            print(f"Script failed with error: {result.returncode}")
        
        await asyncio.sleep(5)

cycle_min_metric = Gauge('validator_cycle_min', 'Election cycle minimum staker')
async def run_cycle_min_metric ():
    while True:
        # Replace 'your_script.py' with the name of your Python script
        cmd = ["/usr/bin/python3", 'scripts/get_cycle_stats.py', '-c', 'etc/config.json', '--metric', 'stake', '--info', 'min']
        result = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await result.communicate()
        
        if result.returncode == 0:
            # Set the metric value to the output of the script
            cycle_min_metric.set(float(stdout.decode().strip()))
        else:
            # Handle any errors here, for example, log them
            print(f"Script failed with error: {result.returncode}")
        
        await asyncio.sleep(5)

election_participation_metric = Gauge('validator_election_participation', 'Election participation')
async def run_election_participation_metric(adnlAddr):
    while True:
        cmd = ["python3", "scripts/check_election_participation.py", "-c", "etc/config.json", adnlAddr]
        result = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await result.communicate()
        
        if result.returncode == 0:
            # Set the metric value to the output of the script
            election_participation_metric.set(float(stdout.decode().strip()))
        else:
            # Handle any errors here, for example, log them
            print(f"Script failed with error: {result.returncode}")
        
        await asyncio.sleep(5)

adnl_address = Info('validator_adnl_address', 'only get once at the start of exporter')
def get_adnl_address():
    with open("/home/allenchan/.local/share/mytoncore/mytoncore.db", 'r') as f:
        data = json.load(f)
    adnlAddr = data.get('adnlAddr', None)

    if adnlAddr is not None:
        # Set the Info metric to the adnlAddr
        adnl_address.info({'adnlAddr': adnlAddr})
        return adnlAddr
    else:
        # Handle any errors here, for example, log them
        print(f"Script failed with error: adnlAddr not found in JSON")

# Need sudo permission
ports_open = Info('validator_ports_open', 'only get once at the start of exporter')
# engine_port = ""
def get_ports_open():
    # global engine_port
    with open("/var/ton-work/db/config.json", 'r') as f:
        data = json.load(f)
    engine = data.get('addrs')[0].get('port', None)
    ls = data.get('liteservers')[0].get('port', None)
    control = data.get('control')[0].get('port', None)

    if engine is not None and ls is not None and control is not None:
        # Set the Info metric to the ports
        ports_open.info({'port_engine': str(engine), 'port_ls': str(ls), 'port_control': str(control)})
        return str(engine)
    else:
        # Handle any errors here, for example, log them
        print(f"Script failed with error: some ports not found in JSON")

validator_port_probing_metric = Gauge('validator_validator_port_probing', 'Validator udp port open')
async def run_validator_port_probing_metric(port_engine):
    response = requests.get('https://api.ipify.org')
    myIpAddr = response.text
    while True:
        cmd = ["nc", "-zvu", myIpAddr, port_engine]
        result = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await result.communicate()        

        if result.returncode == 0:
            # if 'open' in result.stdout:
            if 'succeeded!' in stderr.decode():
                isOpen = 1
            else:
                isOpen = 0
            # Set the metric value to the output of the script
            validator_port_probing_metric.set(float(isOpen))
        else:
            # Handle any errors here, for example, log them
            print(f"Script failed with error: {result.returncode}")
        
        await asyncio.sleep(5)

def run_get_is_mainnet():
    cmd = ['sh', "/usr/bin/lite-client", '-c', 'getconfig']
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if result.returncode == 0:
        stdout_lines = result.stdout.split('\n')
        for line in stdout_lines:
            if 'validators_elected_for:65536' in line:
                return 1
            else: 
                return 0
        print("No line found with 'validators_elected_for:65536'")
    else:
        print(f"Script failed with error: {result.returncode}")  

def generate_ls_local_config():
    cmd = ["sudo", "/usr/bin/python3", "./support/generate_local_config.py", '-o', '/usr/bin/ton/local.config.json']
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if result.returncode == 0:
        print("ls config generated.")
    else:
        print(f"Script failed with error: {result.returncode}")  

async def main():
    # Start an HTTP server to expose the metrics
    start_http_server(8888)
    
    generate_ls_local_config()
    adnlAddr = get_adnl_address()
    port_engine = get_ports_open() # require sudo 
    is_mainnet = run_get_is_mainnet()
    # Update the metric in the background by running the external script
    await asyncio.gather(
        run_external_script(),
        run_cycle_max_metric(),
        run_cycle_min_metric(),
        run_election_participation_metric(adnlAddr),
        run_validator_port_probing_metric(port_engine),
    )

if __name__ == '__main__':
    asyncio.run(main())
