#!/usr/bin/env python3

import subprocess

# TODO use LC class instead of manual filtering
def run():
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

if __name__ == '__main__':
    run()
