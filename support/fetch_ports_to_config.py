#!/usr/bin/env python3
import json

def run():
    with open("/var/ton-work/db/config.json", 'r') as f:
        data = json.load(f)
    engine = data.get('addrs')[0].get('port', None)
    ls = data.get('liteservers')[0].get('port', None)
    control = data.get('control')[0].get('port', None)

    # Read the existing data
    with open('etc/config.json', 'r') as f:
        data = json.load(f)

    # Update the data with the new port information
    data['ports'] = {
            'addrs': engine,
            'liteservers': ls,
            'control': control
        }

    if engine is not None and ls is not None and control is not None:
        # Set the Info metric to the ports
        with open('etc/config.json', 'w') as f:
            json.dump(data, f)
    else:
        # Handle any errors here, for example, log them
        print(f"Script failed with error: some ports not found in JSON")

if __name__ == '__main__':
    run()
