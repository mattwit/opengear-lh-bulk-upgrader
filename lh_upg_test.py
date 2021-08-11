#!/usr/bin/python3
#
# Python script for bulk upgrade of OM's from LH
# Requires a smart group to be defined in LH
# Note: Script will be deprecated by next LH release.
#
# Opengear - Solutions Engineering, 10 August 2021


import requests, json, subprocess, os, time
import creds # conf file with creds and url

# temp for testing - removes https warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


# Globals - Edit these variables to match your environment
group = 'group1'        # Smart group name in LH 
fwVersion = '21.Q2.1'   # Update version - temp note: changed to trigger push
fwName = 'operations_manager-21.Q2.1-production-signed.raucb'    # Update filename


# Create hostfile for node smart group
class getHosts:

    hosts = "node-command -g " + group + " --list-nodes | awk '/address:/ { print $2 }' >> /mnt/nvram/hosts.txt"
    os.system(hosts)
    
    with open("/mnt/nvram/hosts.txt", "r") as f:
        ipaddr = f.read().splitlines()
    f.close()


# Get token for api calls
def createToken(line):

    uri = 'https://' + line + '/api/v2/sessions/'
    data = { 'username' : creds.username, 'password' : creds.password }
    r = requests.post(uri, data=json.dumps(data), verify=False)
    token = json.loads(r.text)['session']

    return token


# Check version and copy update if necessary
def cp2om():

    # Iterate through the node addresses (line) in list ipaddr to check/copy update file
    for line in getHosts.ipaddr:
        
        # Create an api token for each OM
        token = createToken(line)
        headers = { 'Authorization' : 'Token ' + token }

        # Use api to get OM firmware version
        uri = 'https://' + line + '/api/v2/system/version'
        r = requests.get(uri, headers=headers, verify=False)
        h = json.loads(r.text)['system_version']['firmware_version']
        print('\n')
        print(line + '-->' + h)
  
        # Check if OM fw version matches fwVersion
        # Push update file to OM if version don't match
        if h != fwVersion:
            print('\n')
            print('Version ' + h + ' detected on ' + line)
            print('Pushing update file ' + fwName + ' to ' + line)
            print('\n')
            cp = subprocess.run(['node-command', '-a', line, '-s', '/mnt/nvram/' + fwName, '-c', '/mnt/nvram'], stdout=subprocess.PIPE)
            print(cp)
            time.sleep(1)
            print('File copy complete!')
            print('\n')
        # Skip to next OM if versions match
        else:
            print('\n')
            print('OM is already up to date with version ' + line + '. Skipping...')
            print('\n')


# Upgrade OM - temp note: this function needs to wait for the cp2om() to complete before running
def omUpg():

    # iterate through hosts.txt for version
    for line in getHosts.ipaddr:

        upg = subprocess.run(['node-command', '-a', line, 'sudo', 'puginstall', '/mnt/nvram/' + fwName], stdout=subprocess.PIPE)
              
        print(upg)


# Remove temp files and images
def cleanUp():

    print('\n')
    print('Cleaning up...')
    print('\n')

    os.system("rm /mnt/nvram/hosts.txt")

    cmd = "node-command -g " + group + " rm /mnt/nvram/" + fwName
    os.system(cmd)

    print('Done...')
    print('\n')


if __name__ == "__main__":

    cp2om()
    omUpg()
    cleanUp()
