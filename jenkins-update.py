#!/usr/bin/python3
from datetime import datetime as dt
from os import path
from xml.etree import ElementTree as ET
import json
import logging
from collections import defaultdict


# read config or last update
def read_last_update(filename):
    logging.debug('reading last update datetime')
    if path.exists(filename):
        with open(filename) as f:
           last_update = dt.strptime(f.read().strip(), options['dt_format'])
        return last_update
    else:
        return dt(1970,1,1,0,0,0,1)

def set_last_update(filename, last_update):
    with open(filename, 'w') as f:
        f.write(last_update.strftime(options['dt_format']))

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
        if check_snapshot_update_time(repo, last_update): 
            update_required = True
            break
    return update_required

def check_snapshot_update_time(repo, last_update):
    print("checking {0}/{1}".format(repo['dist'],repo['branch']))
    # temp file of xml webapi output
    for update_time in ET.parse("./mockxml/{}rss.xml".format(repo['branch'])).getiterator('updated'):
        jenkins_updated = dt.strptime(update_time.text, '%Y-%m-%dT%H:%M:%SZ')
        print("")
        if  jenkins_updated > last_update:
            print("new update: {}".format(update_time.text))
            return True
    return False


def rsync_call_to_bash(sync_required):
    if sync_required['stable']:
        print("rsync to FTC ....")
    if sync_required['stable'] or sync_required['unstable']:
        print("rsync to CTS ....")

def set_default_options(base_options):
    if not base_options['dt_format']: base_options['dt_format'] = "%Y-%m-%d %H:%M:%S.%f"
    # if not base_options['log_level']: base_options['log_level'] = logging.ERROR
    if not base_options['file_path']: base_options['file_path'] = '.' 


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-c','--config', help="configuration file to use", action='store')
    args = parser.parse_args()
    if args.config:
        with open(args.config, 'r') as configfile:
            options = json.load(configfile)
    else:
        options = {
            'dt_format': "%Y-%m-%d %H:%M:%S.%f",
            'file_path': '.',
            'log_level': logging.ERROR
        }
    set_default_options(options) 
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
        update_file = "{}/jenkins-update-{}.date".format(options['file_path'],branch['name'])
        last_update = read_last_update(update_file)
        if check_if_update_required(branch, last_update):
            update_snapshots(branch)
            sync_required[branch['name']] = True
            set_last_update(update_file, current_datetime)
    rsync_call_to_bash(sync_required)
        
    print("End of program, updated {}".format(sync_required))