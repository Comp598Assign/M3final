import pycurl
import sys
import requests
from flask import Flask, jsonify, request
import os.path
from urllib.parse import urlencode


def cloud_init(url): #initalize default cluster
    r = requests.get(url + '/cloud/initalization')
    print(r.text)
    

def cloud_register_node(url, node_name, pod_id): #TODO specify pod type in request
    r = requests.post(url + '/cloud/' + str(pod_id) + '/nodes/' + node_name)
    print(r.text)

def cloud_remove_node(url, node_name, pod_id): #dispatch request to appropriate pod
    r = requests.delete(url + '/cloud/' + pod_id + '/rm/' + node_name)
    print(r.text)


def cloud_launch_pod(url, pod_id):
    #launch pod
    r = requests.get(url + '/cloud/' + pod_id + '/launch')
    print(r.text)
    return 0


def cloud_resume_pod(url, pod_id):
    r = requests.get(url + '/cloud/' + pod_id + '/resume')
    print(r.text)
    #resume pod
    #If there are any nodes with the “ONLINE” status, then the Load Balancer should include these in its configuration so that it can start sending traffic through to this node again.
    return 0


def cloud_pause_pod(url, pod_id):
    r = requests.get(url + '/cloud/' + pod_id + '/pause')
    print(r.text)
    #All the nodes with the “ONLINE” status inside this pod are removed and the Load Balancer is notified so that no more incoming client request on this pod will receive a response
    return 0


def cloud_request_pod(url, pod_id):
    r = requests.get(url + '/cloud/' + pod_id + '/usage')
    print(r.text)
    #Helper method to request all the cpu_usage of individual container.
    return 0

def cloud_lower_threshold (url,name,value):
    r = requests.get(url+'/cloud/elasticity/lower/'+name+'/'+value)
    print(r.text)
def cloud_upper_threshold (url,name,value):
    r = requests.get(url+'/cloud/elasticity/upper/'+name+'/'+value)
    print(r.text)
def cloud_elasticity_enable(url,name,lower_size,upper_size):
    r = requests.post(url+'/cloud/elasticity/enable/'+name+'/'+lower_size+'/'+upper_size)
    print(r.text)
def cloud_elasticity_disable(url,name):
    r = requests.get(url+'/cloud/elasticity/disable/'+name)
    print(r.text)
def main():
    rm_url = sys.argv[1]
    cloud_init(rm_url)
    while (1):
        command = input('$ ')
        commandstr = command.split()
        if command == 'cloud init': #TODO: init three pod
            cloud_init(rm_url)
        elif command.startswith('cloud register') and len(commandstr)==4:
            cloud_register_node(rm_url,commandstr[2],commandstr[3])
        elif command.startswith('cloud rm') and len(commandstr)==4:
            cloud_remove_node(rm_url,commandstr[2],commandstr[3])
        elif command.startswith('cloud launch') and len(commandstr)==3:
            #launch pod
            cloud_launch_pod(rm_url,commandstr[2])
        elif command.startswith('cloud resume') and len(commandstr)==3:
            cloud_resume_pod(rm_url,commandstr[2])
        elif command.startswith('cloud pause') and len(commandstr)==3:
            cloud_pause_pod(rm_url,commandstr[2])
        elif command.startswith('cloud request') and len(commandstr)==3:
            cloud_request_pod(rm_url,commandstr[2])
        elif command.startswith('cloud elasticity lower_threshold') and len(commandstr)==5:
            cloud_lower_threshold(rm_url,commandstr[3],commandstr[4])
        elif command.startswith('cloud elasticity upper_threshold') and len(commandstr)==5:
            cloud_upper_threshold(rm_url,commandstr[3],commandstr[4])
        elif command.startswith('cloud elasticity enable') and len(commandstr)==6:
            cloud_elasticity_enable(rm_url,commandstr[3],commandstr[4],commandstr[5])
        elif command.startswith('cloud elasticity disable') and len(commandstr)==4:
            cloud_elasticity_disable(rm_url,commandstr[3])
        else:
            print("command does not exist")
if __name__ == '__main__':
    main()