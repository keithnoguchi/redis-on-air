#!/usr/bin/env python

import os
import json
import argparse
import subprocess
import sys
import libvirt

def main():
    inventory = {'all': {'hosts': [],
                         'vars': {'ansible_user': os.environ['USER']}}}
    inventory['host'] = {'hosts': ['localhost'],
                         'vars': {'ansible_connection': 'local'}}
    inventory['head'] = head()
    inventory['work'] = work()

    master_ip = ''
    hostvars = {}
    for type in ['head', 'work']:
        for host in inventory[type]['hosts']:
            num = int(''.join(filter(str.isdigit, host)))
            inventory['all']['hosts'].append(host)
            hostvars[host] = {'name': host}
            if host == inventory['work']['hosts'][0]:
                # First worker as the redis master.
                master_ip = '172.31.255.%d' % num
                hostvars[host] = {'master': True,
                        'master_ip': master_ip}
            elif master_ip != '':
                hostvars[host] = {'master': False,
                        'master_ip': master_ip}

    # https://github.com/ansible/ansible/commit/bcaa983c2f3ab684dca6c2c2c8d1997742260761
    inventory['_meta'] = {'hostvars': hostvars}

    parser = argparse.ArgumentParser(description="KVM inventory")
    parser.add_argument('--list', action='store_true',
                        help="List KVM inventory")
    parser.add_argument('--host', help='List details of a KVM inventory')
    args = parser.parse_args()

    if args.list:
        print(json.dumps(inventory))
    elif args.host:
        print(json.dumps(hostvars.get(args.host, {})))


def head():
    nodes = {'hosts': []}

    c = libvirt.openReadOnly("qemu:///system")
    if c != None:
        for i in c.listDomainsID():
            dom = c.lookupByID(i)
            if dom.name().startswith('head') == True:
                nodes['hosts'].append(dom.name())

    if len(nodes['hosts']) == 0:
        nodes['hosts'].append('head10')

    return nodes


def work():
    nodes = {'hosts': []}

    c = libvirt.openReadOnly("qemu:///system")
    if c != None:
        for i in c.listDomainsID():
            dom = c.lookupByID(i)
            if dom.name().startswith('work'):
                nodes['hosts'].append(dom.name())

    return nodes


if __name__ == "__main__":
    main()
