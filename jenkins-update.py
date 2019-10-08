#!/usr/bin/python3
from datetime import datetime as dt
from os import path
from xml.etree import ElementTree as ET

options = {
    'DT_FORMAT': '%Y-%m-%d %H:%M:%S.%f',
    'file_locations': '.'
} 
# read config or last update
def read_last_update(filename):
    print('reading last update datetime')
    if path.exists(filename):
        with open(filename) as f:
           last_update = dt.strptime(f.read().strip(), options['DT_FORMAT'])
        return last_update
    else:
        return dt(1970,1,1,0,0,0,1)

def set_last_update(filename, last_update):
    with open(filename, 'w') as f:
        f.write(last_update.strftime(options['DT_FORMAT']))

# update snapshots and publish
def update_snapshots(branch):
    print("udating the following repos:\n{}".format(branch['repos']))

def check_if_update_required(branch_repos, last_update):
    update_required = False
    print("checking {0} branch for updates since {1}....".format(branch['name'], last_update))
    if last_update.day < dt.today().day:
        print("first snapshot of the day")
        update_required = True
    for repo in branch['repos']:
        if last_update < check_snapshot_update_time(repo): 
            update_required = True
            break
    return update_required

def check_snapshot_update_time(repo):
    print("checking {0}/{1}".format(repo['dist'],repo['branch']))

    # temp mock of json output
    latest_jenkins_update = dt.strptime(ET.parse("ci-jenkins-{}-{}.xml".format(repo['dist'],repo['branch'])).find('date').text, '%Y-%m-%d %H:%M:%S')
    return latest_jenkins_update

def rsync_call_to_bash(sync_required):
    if sync_required['stable']:
        print("rsync to FTC ....")
    if sync_required['stable'] or sync_required['unstable']:
        print("rsync to CTS ....")

if __name__ == '__main__':
    current_datetime = dt.now()
    branches = [ {'name': 'stable',
                    'repos': [{'branch': 'fc1', 'dist': 'jessie'},
                            {'branch': 'fc2', 'dist': 'stretch'},
                            {'branch': 'fc3', 'dist': 'buster'}]},
                {'name': 'unstable', 
                    'repos': [{'branch': 'unstable', 'dist': 'jessie'},
                            {'branch': 'uc2', 'dist': 'stretch'},
                            {'branch': 'uc3', 'dist': 'buster'}]
                } ]
    sync_required = {'stable': False, 'unstable': False }
    for branch in branches:
        print("branch name: {}".format(branch['name']))
        last_update = read_last_update("jenkins-update-{}.date".format(branch['name']))
        if check_if_update_required(branch, last_update):
            update_snapshots(branch)
            sync_required[branch['name']] = True
            update_file = "jenkins-update-{}.date".format(branch['name'])
            set_last_update(update_file, current_datetime)
    rsync_call_to_bash(sync_required)
        
    print("End of program, updated {}".format(sync_required))