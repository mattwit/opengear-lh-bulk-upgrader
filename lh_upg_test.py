#/usr/bin/python3
# This is an initial template for bulk upgrade from LH
# 

import requests, json, subprocess, os
import creds # conf file with creds and url

# temp for testing - removes https warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# globals
group = 'group2'        # Smart group name in LH 
fwVersion = '21.Q2.0'   # Update version - temp note: changed to trigger push
fwName = 'test.file'    # Update filename


# Get token for api calls
def createToken():

    uri = 'https://' + host + '/api/v2/sessions/'
    data = { 'username' : creds.username, 'password' : creds.password }
    r = requests.post(uri, data=json.dumps(data), verify=False)
    token = json.loads(r.text)['session']

    return token


# Create hostfile for group
def getHosts():

    os.system("node-command -g group2 --list-nodes | awk '/address:/ { print $2 }' >> /mnt/nvram/hosts.txt")

    print('Retrieving list of Nodes for ' + group)

    os.system("cat /mnt/nvram/hosts.txt")
    

# Check version and copy update if necessary
def cp2om():

    # temp note: logic not quite there to iterate through all hosts in group

    # api stuff
    token = createToken()

    with open("/mnt/nvram/hosts.txt", "r") as f:
        ipaddr = f.read().splitlines()

    # iterate through hosts.txt for version
    for line in ipaddr:

        try:
            headers = { 'Authorization' : 'Token ' + token }
            uri = 'https://' + line + '/api/v2/system/version'
            r = requests.get(uri, headers=headers, verify=False)
            h = json.loads(r.text)['system_version']['firmware_version']
            
        except Exception:
            pass
    
        print(line + '-->' + h)
  
        if h != fwVersion:
            print('\n')
            print('Version ' + h + ' detected on ' + line)
            print('Pushing update version ' + h + 'to ' + line)
            print('\n')
            cp = subprocess.run(['node-command', '-g', group, '-s', '/mnt/nvram/' + fwName, '-c', '/mnt/nvram'], stdout=subprocess.PIPE)
            print(cp)
        else:
            print('\n')
            print('OM is already up to date with ' + group + '. Skipping...')
            print('\n')


# Upgrade OM - temp note: this function needs to wait for the cp2om() to complete before running
def omUpg():

    with open("/mnt/nvram/hosts.txt", "r") as f:
        ipaddr = f.read().splitlines()

    # iterate through hosts.txt for version
    for line in ipaddr:

        try:
            upg = "node-command -g " + group + " sudo puginstall --reboot-after /mnt/nvram/" + fwName
              
        except Exception:
            pass

    upg = "node-command -g " + group + " sudo puginstall --reboot-after /mnt/nvram/" + fwName

    print(upg)



if __name__ == "__main__":

    getHosts()
    cp2om()
    #omUpg()

    # Cleanup 
    os.system("rm /mnt/nvram/hosts.txt")
