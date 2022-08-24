#!/usr/bin/python3
#
# lh_bulk_upgrade.py (v.01)
# Opengear - Solutions Engineering, 1 Sept 2021
#
# Python script for bulk upgrade of OM's from LH via CLI
# Requires a smart group to be defined in LH

import requests
import json
import subprocess
import os
import time
import argparse
import getpass

# temp for testing - removes https warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# COMMENTED OUT for argparse#
# Globals - Edit these variables to match your environment
#group = 'group1'        # Smart group name in LH 
#fwVersion = '21.Q2.1'   # Update version - temp note: changed to trigger push
#fwName = 'operations_manager-21.Q2.1-production-signed.raucb'    # Update filename - place in /mnt/nvram

print('\nLighthouse CLI Bulk Upgrader for OMs (v.01, 1 Sept 2021)\n')
print('***** IGNORE REMOVE FILE OR CLEANUP ERRORS. STILL WIP *****')

# cli arguments when launching script
parser = argparse.ArgumentParser()
parser.add_argument('--copy', help='Copy image to OMs', action="store_true")
parser.add_argument('-g', default=argparse.SUPPRESS, help='Smart Group ID')
parser.add_argument('-v', default=argparse.SUPPRESS, help='Firmware Version (e.g. 21.Q2.0)')
parser.add_argument('-f', default=argparse.SUPPRESS, help='Firmware filename (.raucb file)')
args = parser.parse_args()

# globals from args
group = args.g
version = args.v
fName = args.f


# Create hostfile for node smart group
def hostFile():

    subprocess.run(['rm', '/mnt/nvram/hosts.txt'], stdout=subprocess.PIPE)

    hosts = "node-command -g " + group + " --list-nodes | awk '/address:/ { print $2 }' >> /mnt/nvram/hosts.txt"
    os.system(hosts)    
    with open("/mnt/nvram/hosts.txt", "r") as f:
        ipaddr = f.read().splitlines()
    f.close()

    return ipaddr


# Get token for api calls
def createToken(line,username,password):

    uri = f'https://{line}/api/v2/sessions/'
    data = { 'username' : username, 'password' : password }
    r = requests.post(uri, data=json.dumps(data), verify=False)
    token = json.loads(r.text)['session']

    return token

# Check current firmware on OMs
def checkVersion():

    ipaddr = hostFile()

    print('\n')
    print('Please enter OM credentials...')
    username = input('Username: ')
    password = getpass.getpass()
    print('\n')

    for line in ipaddr:
        
        # Create an api token for each OM
        token = createToken(line,username,password)
        headers = { 'Authorization' : 'Token ' + token }

        # Use api to get OM firmware version
        uri = f'https://{line}/api/v2/system/version'
        r = requests.get(uri, headers=headers, verify=False)
        h = json.loads(r.text)['system_version']['firmware_version']

        upgList = []
        if h != version:
            upgList = [line]
            print(f'{line} running version {h} -- upgrade available' )
        else:
            print(f'{line} running version {h}')

    return upgList


# Check version and copy update if necessary
def cp2om():

    upgList = checkVersion()

    upgCount = len(upgList)

    if upgCount != 0:
        upgCont = input(f'\n{upgCount} nodes need the update file. Push file to nodes? (y/n) ')
        if upgCont == 'y':
            print(f'\nOK...Pushing file to {upgCount} nodes...\n')
            for line in upgList:
                print(f'Pushing update file {fName} to {line}...')
                print('This will take a few minutes...\n')
                subprocess.run(['node-command', '-a', line, '-s', '/mnt/nvram/' + fName, '-c', '/mnt/nvram'], stdout=subprocess.PIPE)
                time.sleep(1)
                print('File copy complete!\n')
        else:
            print('\nOK...quitting...')
            cleanUp()
            exit()
    else:
        print('\nNo nodes need upgrading...quitting..')
        exit()


# Upgrade OM - temp note: this function needs to wait for the cp2om() to complete before running
def omUpg():

    upgList = checkVersion()

    upgCount = len(upgList)

    if upgCount != 0:
        upgCont = input(f'\n{upgCount} nodes ready to upgrade, continue to upgrade? (y/n) ')
        if upgCont == 'y':
            print(f'\nOK...upgrading {upgCount} nodes...\n')
            for line in upgList:
                subprocess.run(['node-command', '-a', line, 'sudo', 'puginstall', '/mnt/nvram/' + fName], stdout=subprocess.PIPE)
        else:
            print('\nOK...quitting..')
    else:
        print('\nNo nodes need upgrading...quitting..')


# Remove temp files and images
def cleanUp():

    print('\n')
    print('Cleaning up...')
    
    subprocess.run(['rm', '/mnt/nvram/hosts.txt'], stdout=subprocess.PIPE)

    os.system(f'node-command -q -g {group} rm /mnt/nvram/{fName}')

    print('CleanUp done...\n')


if __name__ == "__main__":

    # check optional args
    if args.copy:
        cp2om()
        exit()
    else:
        pass
    
    print(f'Smart Group:      {group}')
    print(f'Upgrade Version:  {version}')
    print(f'Upgrade Filename: {fName}')

    argCheck = input('\nDo these look correct? (y/n) ')
    if argCheck == 'y':
        print('\nOK...starting up...')
    else:
        print('\nOK...quitting...\n')
        subprocess.run(['rm', '/mnt/nvram/hosts.txt'])
        exit()

    omUpg()
    cleanUp()