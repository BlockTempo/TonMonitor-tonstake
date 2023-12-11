#!/usr/bin/env python3

import os 
import subprocess
from prometheus_client import start_http_server, Gauge, Info
import time
import json
import requests
import re
import asyncio
import aiohttp

# Create a Gauge metric
gauge_metric = Gauge('validator_ls_sync', 'Time to last block of LS')
# Function to run the external Python script and get its output
async def run_ls_sync(port_ls):
    while True:
        cmd = ["python3", "scripts/check_ls_sync.py", "-c", "etc/config.json", "-a", "127.0.0.1:%s" % port_ls, "-p", "/var/ton-work/keys/liteserver.pub"] #adhoc use pub 
        result = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await result.communicate()        

        if result.returncode == 0:
            # Set the metric value to the output of the script
            gauge_metric.set(float(stdout.decode().strip()))
        else:
            # Handle any errors here, for example, log them
            print(f"Script failed with error: {result.returncode}")
            gauge_metric.set(float(-1))
        
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
    with open("/home/allenchan/.local/share/mytoncore/mytoncore.db", 'rb') as f:
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
    with open("etc/config.json", 'rb') as f:
        data = json.load(f)
    data = data.get('ports')
    engine = data.get('addrs', None)
    ls = data.get('liteservers', None)
    control = data.get('control', None)
    
    if engine is not None and ls is not None and control is not None:
        # Set the Info metric to the ports
        ports_open.info({'port_engine': str(engine), 'port_ls': str(ls), 'port_control': str(control)})
        return str(engine), str(ls), str(control)
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
 
time_to_sync_metric = Gauge('validator_time_to_sync', 'Time to sync')
async def run_time_to_sync_metric(port_control):
    while True:
        cmd = ['/usr/bin/ton/validator-engine-console/validator-engine-console', '-k', '/var/ton-work/keys/client', '-p', '/var/ton-work/keys/server.pub', '-a', '127.0.0.1:%s' % port_control, '-v', '0', '--cmd', 'getstats']
        result = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await result.communicate()
        
        if result.returncode == 0:
            output = stdout.decode().strip()

            # Extract unixtime and masterchainblocktime
            unixtime = int(re.search(r'unixtime\s+(\d+)', output).group(1))
            masterchainblocktime = int(re.search(r'masterchainblocktime\s+(\d+)', output).group(1))
            # Calculate the delta
            delta = unixtime - masterchainblocktime
            time_to_sync_metric.set(delta)
        else:
            print(f"Script failed with error: {result.returncode}")
        await asyncio.sleep(5)

mytoncore_lockfile_exist_metric = Gauge('mytoncore_lockfile_exist', '')

async def run_mytoncore_lockfile_exist_metric():
    while True:
        # Check if the file ".local" exists
        local_file_exists = os.path.exists('/home/allenchan/.local/share/mytoncore/mytoncore.db.lock')
        # print(f'The file .local exists: {local_file_exists}')

        if local_file_exists != None:
            mytoncore_lockfile_exist_metric.set(local_file_exists)
        else:
            print(f"Script failed with error")
        await asyncio.sleep(5)

# from scripts import get_is_mainnet
async def main():
    # Start an HTTP server to expose the metrics
    start_http_server(8888)
    
    # generate_ls_local_config()
    adnlAddr = get_adnl_address()
    port_engine, port_ls, port_control = get_ports_open() 
    # is_mainnet = run_get_is_mainnet()
    # is_mainnet =  get_is_mainnet.run()
    # print(is_mainnet)
    # Update the metric in the background by running the external script
    await asyncio.gather(
        run_ls_sync(port_ls),
        run_cycle_max_metric(),
        run_cycle_min_metric(),
        run_election_participation_metric(adnlAddr),
        run_validator_port_probing_metric(port_engine),
        run_time_to_sync_metric(port_control),
        run_mytoncore_lockfile_exist_metric()
    )

if __name__ == '__main__':
    asyncio.run(main())

# TODO: get config itself, without sudo permissions  
# ['/usr/bin/ton/validator-engine-console/validator-engine-console', '-k', '/var/ton-work/keys/client', '-p', '/var/ton-work/keys/server.pub', '-a', '127.0.0.1:51496', '-v', '0', '--cmd', 'getconfig']
