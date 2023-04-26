from io import BytesIO
import subprocess
import time
from flask import Flask, jsonify, request, render_template
import pycurl
import sys
import json
from threading import Thread
import requests
import random
import string
from urllib.parse import urlencode
from dotenv import load_dotenv
load_dotenv()
import os

cURL=pycurl.Curl()

app = Flask(__name__)
global from_rm
from_rm = False

elasticity_from_rm = {"light_pod" : False, "medium_pod":False, "heavy_pod": False}

proxy_url = {}
resource_manager_url = {}
elasticity_status = {"light_pod" : {'is_on' : False, 'lower' : 0, 'upper' : 40, "lower_size":0 ,"upper_size":20}, 
                     "medium_pod" : {'is_on' : False, 'lower' : 0, 'upper' : 40, "lower_size":0 ,"upper_size":15},
                     "heavy_pod" : {'is_on' : False, 'lower' : 0, 'upper' : 40, "lower_size":0 ,"upper_size":10}}



proxy_url['light_pod'] = os.environ.get("light_proxy_ip")
proxy_url['medium_pod'] = os.environ.get("medium_proxy_ip")
# proxy_url['heavy_pod'] = os.environ.get("heavy_proxy_ip")

#add env for self call
resource_manager_url['resource_manager_url'] = os.environ.get('resource_manager_url')

jobs =[]
jobidcounter_fornextjob = 0
class Job:
    def __init__(self,status,file,pNode = None):
        global jobidcounter_fornextjob 
        self.id = jobidcounter_fornextjob
        self.status = status
        self.file = file
        self.node_running_on = pNode
        jobidcounter_fornextjob+=1
    def __str__(self):
        if self.node_running_on == None:
            return "Registerd Job waiting in Queque"
        else:
            return "Job id:"+ self.id +"running in Node: " + self.node_running_on


#Function to add/remove containers to make them stay within bounds while the elasticity manager is enable
def add_remove_helper(upper_bound, lower_bound, pod_size, pod_name):
    name_counter = 0
    while(int(pod_size) > int(upper_bound)): #if pod_size > upper_bound, remove pods
        node_datas = json.loads(requests.get(proxy_url[pod_name] + '/cloudproxy/allPods/all').text)
        node_datas.pop(0)
        node_to_remove = random.choice(node_datas)['node']
        requests.delete(resource_manager_url['resource_manager_url']+'/cloud/'+ pod_name + '/rm/' + node_to_remove)
        pod_size = pod_size - 1

    while(int(pod_size) < int(lower_bound)): #if pod_size < upper_bound, add pods
        #add new nodes
        name = str(name_counter) + str(name_counter) + str(name_counter)
        requests.post(proxy_url[pod_name] + '/cloudproxy/' + pod_name + '/nodes/' + name)
        requests.get(resource_manager_url['resource_manager_url']+'/cloud/' + pod_name + '/launch/' + name)
        name_counter = name_counter + 1
        pod_size = pod_size + 1



def usage_monitor_manager1():
    while(True):
        time.sleep(1)  #After finished, we need to also make sure that the upper and lower size cannot be violated
    
        pod_name = "light_pod"
        if elasticity_status[pod_name]['is_on']:
            elasticity_from_rm[str(pod_name)] = True
            ##### When elasticity manager is enable, the strict upper lower bounds need to be enforced first,
            ##### And not be violated after.
            pod_size = (requests.get(proxy_url[pod_name] + '/cloudproxy/pod_size')).json()['pod_size']

            #Use function to make num of nodes within limits
            add_remove_helper(elasticity_status[pod_name]["upper_size"], elasticity_status[pod_name]["lower_size"],
            pod_size, pod_name)
            #####
            light_pod_response=requests.get(proxy_url[pod_name] + '/cloudproxy/usage')
            if light_pod_response.status_code == 200:
                light_cpu_data=light_pod_response.json()
                print(light_cpu_data["cpu_data"], light_cpu_data["total_usage"])
                #if pod_size > elasticity_status[pod_name]["upper"], you should not be able to add one more pod
                if float(light_cpu_data["total_usage"]) > float(elasticity_status[pod_name]['upper']) and (int(pod_size) <int(elasticity_status[pod_name]["upper_size"])):
                    
                    name = ''.join(random.choices(string.ascii_lowercase, k=4))
                    requests.post(proxy_url[pod_name] + '/cloudproxy/' + pod_name + '/nodes/' + name)
                    requests.get(resource_manager_url['resource_manager_url']+'/cloud/' + pod_name + '/launch/' + name)
                #if pod_size > elasticity_status[pod_name]["lower"] you shouldn't be able to remove pod
                #maybe print message to indicate
                elif float(light_cpu_data["total_usage"]) <float(elasticity_status[pod_name]['lower'])  and (int(pod_size) >int(elasticity_status[pod_name]["lower_size"])):
                    data = json.loads(requests.get(proxy_url[pod_name] + '/cloudproxy/allPods/all').text)
                    data.pop(0)
                    node_to_remove = random.choice(data)['node']
                    requests.delete(resource_manager_url['resource_manager_url']+'/cloud/' + pod_name + '/rm/' + node_to_remove)
                
def usage_monitor_manager2():
    while(True):
        time.sleep(1)  #After finished, we need to also make sure that the upper and lower size cannot be violated
        pod_name = "medium_pod"
        if elasticity_status[pod_name]['is_on']:
            elasticity_from_rm[str(pod_name)] = True
            ##### When elasticity manager is enable, the strict upper lower bounds need to be enforced first,
            ##### And not be violated after.
            pod_size = (requests.get(proxy_url[pod_name] + '/cloudproxy/pod_size')).json()['pod_size']

            #Use function to make num of nodes within limits
            add_remove_helper(elasticity_status[pod_name]["upper_size"], elasticity_status[pod_name]["lower_size"],
            pod_size, pod_name)
            #####
            light_pod_response=requests.get(proxy_url[pod_name] + '/cloudproxy/usage')
            if light_pod_response.status_code == 200:
                light_cpu_data=light_pod_response.json()
                print(light_cpu_data["cpu_data"], light_cpu_data["total_usage"])
                #if pod_size > elasticity_status[pod_name]["upper"], you should not be able to add one more pod
                if float(light_cpu_data["total_usage"]) > float(elasticity_status[pod_name]['upper']) and (int(pod_size) <int(elasticity_status[pod_name]["upper_size"])):
                    
                    name = ''.join(random.choices(string.ascii_lowercase, k=4))
                    requests.post(proxy_url[pod_name] + '/cloudproxy/' + pod_name + '/nodes/' + name)
                    requests.get(resource_manager_url['resource_manager_url']+'/cloud/' + pod_name + '/launch/' + name)
                #if pod_size > elasticity_status[pod_name]["lower"] you shouldn't be able to remove pod
                #maybe print message to indicate
                elif float(light_cpu_data["total_usage"]) <float(elasticity_status[pod_name]['lower'])  and (int(pod_size) >int(elasticity_status[pod_name]["lower_size"])):
                    data = json.loads(requests.get(proxy_url[pod_name] + '/cloudproxy/allPods/all').text)
                    data.pop(0)
                    node_to_remove = random.choice(data)['node']
                    requests.delete(resource_manager_url['resource_manager_url']+'/cloud/' + pod_name + '/rm/' + node_to_remove)


# def usage_monitor_manager3():
#     while(True):
#         time.sleep(1)  #After finished, we need to also make sure that the upper and lower size cannot be violated
#         pod_name = "heavy_pod"
#         if elasticity_status[pod_name]['is_on']:
#             elasticity_from_rm[str(pod_name)] = True
#             ##### When elasticity manager is enable, the strict upper lower bounds need to be enforced first,
#             ##### And not be violated after.
#             pod_size = (requests.get(proxy_url[pod_name] + '/cloudproxy/pod_size')).json()['pod_size']

#             #Use function to make num of nodes within limits
#             add_remove_helper(elasticity_status[pod_name]["upper_size"], elasticity_status[pod_name]["lower_size"],
#             pod_size, pod_name)
#             #####
#             light_pod_response=requests.get(proxy_url[pod_name] + '/cloudproxy/usage')
#             if light_pod_response.status_code == 200:
#                 light_cpu_data=light_pod_response.json()
#                 print(light_cpu_data["cpu_data"], light_cpu_data["total_usage"])
#                 #if pod_size > elasticity_status[pod_name]["upper"], you should not be able to add one more pod
#                 if float(light_cpu_data["total_usage"]) > float(elasticity_status[pod_name]['upper']) and (int(pod_size) <int(elasticity_status[pod_name]["upper_size"])):
                    
#                     name = ''.join(random.choices(string.ascii_lowercase, k=4))
#                     requests.post(proxy_url[pod_name] + '/cloudproxy/' + pod_name + '/nodes/' + name)
#                     requests.get(resource_manager_url['resource_manager_url']+'/cloud/' + pod_name + '/launch/' + name)
#                 #if pod_size > elasticity_status[pod_name]["lower"] you shouldn't be able to remove pod
#                 #maybe print message to indicate
#                 elif float(light_cpu_data["total_usage"]) <float(elasticity_status[pod_name]['lower'])  and (int(pod_size) >int(elasticity_status[pod_name]["lower_size"])):
#                     data = json.loads(requests.get(proxy_url[pod_name] + '/cloudproxy/allPods/all').text)
#                     data.pop(0)
#                     node_to_remove = random.choice(data)['node']
#                     requests.delete(resource_manager_url['resource_manager_url']+'/cloud/' + pod_name + '/rm/' + node_to_remove)                



def get_av_node():
    response = requests.get(proxy_url+'/cloudproxy/get_nextav_node')
    data = response.json()
    return data["av_node"]

def get_proxy_url_no_port(pod_id):
    return proxy_url[pod_id].split(':')[1].strip('/')


@app.route('/dashboard')
def dashboard():
    return render_template("Dashboard.html")

@app.route('/nodes/<pod_id>')
def nodes(pod_id):
    str = requests.get(proxy_url[pod_id] + '/cloudproxy/' + pod_id + '/allNodes')
    #return json.dumps(str.json())
    print(str.json)
    return json.dumps(str.json())

@app.route('/cloud/initalization')
def cloud_init():
    success = True
    for url in proxy_url.values():
        response = requests.get(url + '/cloudproxy/initalization')
        if response.json()["response"] != 'success':
            success = False

    if success:
        result = 'successfully created light, medium and heavy resource pods'
    else: 
        result = 'initialization failed'

    return jsonify({"response" : result})
    

@app.route('/cloud/<pod_id>/nodes/<name>', methods = ['POST'])
def cloud_node(pod_id, name):
    if request.method == "POST":
        if elasticity_status[pod_id]['is_on']:  #if now the elasticity manager is on, unable to add node
            return jsonify({"response":"Declined to register node while elasticity manager is on"})

        response = requests.post(proxy_url[pod_id] + '/cloudproxy/' + pod_id + '/nodes/' + name)
        return response.json()


@app.route('/cloud/<pod_id>/rm/<name>', methods = ['DELETE'])
def cloud_rm_node(pod_id, name):
    if request.method == "DELETE":
        if elasticity_status[pod_id]['is_on'] and (not elasticity_from_rm[str(pod_id)]):  #if now the elasticity manager is on, unable to remove node
            return jsonify({"response":"Declined to remove node while elasticity manager is on"})     
        elasticity_from_rm[str(pod_id)] = False
        response = requests.delete(proxy_url[pod_id] + '/cloudproxy/nodes/' + name)
        data = response.json()

        if data["result"] == "failure":
            return data
        
        elif data["result"] == "success" and data["status"] == "ONLINE":
            disable_cmd = "echo 'experimental-mode on; set server " + pod_id.split('_')[0] + "-servers/" + data['name'] + ' state maint ' + "' | sudo socat stdio /run/haproxy/admin.sock"
            subprocess.run(disable_cmd, shell = True, check = True)
            
            del_cmd = "echo 'experimental-mode on; del server " + pod_id.split('_')[0] + "-servers/" + data['name'] + "' | sudo socat stdio /run/haproxy/admin.sock"
            subprocess.run(del_cmd, shell = True, check = True)
            
            msg = ("Removed node %s running on port %s" % (data['name'], data['port'])) 
            return jsonify({"result" : "success", "response" : msg})
        
        return jsonify({"result" : "success", "response" : "Removed node " + data['name']})




@app.route('/cloud/<pod_id>/launch', defaults={'node_name' : None}, methods=['GET'])
@app.route('/cloud/<pod_id>/launch/<node_name>', methods=['GET'])
def cloud_launch_pod(pod_id, node_name):
    if request.method == "GET":
        if node_name is None:
            if elasticity_status[pod_id]['is_on']:  #if now the elasticity manager is on, unable to launch node
                return jsonify({"response":"Declined to launch node while elasticity manager is on"}) 
            else:
                response = requests.get(proxy_url[pod_id] + '/cloudproxy/launch')
                data = response.json()
        else:
            response = requests.get(proxy_url[pod_id] + '/cloudproxy/launch/' + node_name)
            data = response.json()

        if data['response'] == 'success':
            
            add_cmd = "echo 'experimental-mode on; add server " + pod_id.split('_')[0] + "-servers/" + data['name'] + ' ' + get_proxy_url_no_port(pod_id) + ":" + data["port"] + "'| sudo socat stdio /run/haproxy/admin.sock"
            subprocess.run(add_cmd, shell = True, check = True)

            enable_cmd = "echo 'experimental-mode on; set server " + pod_id.split('_')[0] + "-servers/" + data['name'] + ' state ready ' + "' | sudo socat stdio /run/haproxy/admin.sock"
            subprocess.run(enable_cmd, shell = True, check = True)

            msg = ('Successfully launched node: %s under %s pod on port %s, status: %s' % (data['name'], pod_id.split('_')[0], data['port'], data['status']))
        
        else:
            msg = data['result']
        #this is for test purpose, need to be removed at the end
  #      elasticity_status["light_pod"]['is_on']=True
        ########
        return jsonify({'response' : msg})
    
    
@app.route('/cloud/<pod_id>/resume',methods=['GET'])
def cloud_resume_pod(pod_id):
    if request.method == "GET":
        response = requests.get(proxy_url[pod_id] + '/cloudproxy/online_nodes')
        data = response.json()
        for name in data['node_list']:
            enable_cmd = "echo 'experimental-mode on; set server " + pod_id.split('_')[0] + "-servers/" + name + ' state ready ' + "' | sudo socat stdio /run/haproxy/admin.sock"
            subprocess.run(enable_cmd, shell = True, check = True)

        return jsonify({'response' : pod_id + " resumed"})


@app.route('/cloud/<pod_id>/pause',methods=['GET'])
def cloud_pause_pod(pod_id):
    if request.method == "GET":
        response = requests.get(proxy_url[pod_id] + '/cloudproxy/online_nodes')
        data = response.json()
        for name in data['node_list']:
            disable_cmd = "echo 'experimental-mode on; set server " + pod_id.split('_')[0] + "-servers/" + name + ' state maint ' + "' | sudo socat stdio /run/haproxy/admin.sock"
            subprocess.run(disable_cmd, shell = True, check = True)

        return jsonify({'response' : pod_id + " paused"})


@app.route('/cloud/<pod_id>/usage',methods=['GET'])
def cloud_request_pod(pod_id):
    if request.method == "GET":
        response = requests.get(proxy_url[pod_id] + '/cloudproxy/' + pod_id + '/usage')
        cpu_data = response.json()
        print(cpu_data["cpu_data"], cpu_data["total_usage"])

    return jsonify({'response' : pod_id + " nodes' cpu status printed"})    


#debug hao fan
@app.route('/cloud/elasticity/enable/<pod_name>/<lower_size>/<upper_size>',methods =['POST'])
def cloud_elasticity_enable(pod_name,lower_size,upper_size):
    #Validate lower, upper size
    if not(int(upper_size) >= int(lower_size) > 0):
        return jsonify({"response":"Invalid lower upper bound, [upper_size >= lower_size >0] required"})
    #set all enable attributes
    elasticity_status[pod_name]["is_on"] = True #I decide to put logic in monitor, cause the elasticity is easier
    #to be handled in other thred
    elasticity_status[pod_name]["upper_size"] = upper_size
    elasticity_status[pod_name]["lower_size"] = lower_size
    #call 
    elasticity_from_rm[str(pod_name)] = True
    bounds_setter_response = requests.post(proxy_url[pod_name]+'/cloud/elasticity/size/'+lower_size+'/'+upper_size)
    return (bounds_setter_response.json())

@app.route('/cloud/elasticity/disable/<pod_name>')
def cloud_elasticity_disable(pod_name):
    if not elasticity_status[pod_name]['is_on']:
        return jsonify({'response' : "Unapplicable, Aldready diable, cannot diable again"})
    elasticity_status[pod_name]['is_on'] = False
    upper_bound = 0
    if (pod_name == "light_pod"):
        upper_bound = 3 #for test purpose
    elif (pod_name == "medium_pod"):
        upper_bound = 15
    elif(pod_name == "heavy_pod"):
        upper_bound = 2 #for demonstration purpose

    elasticity_from_rm[str(pod_name)] = False
    pod_size = (requests.get(proxy_url[pod_name] + '/cloudproxy/pod_size')).json()['pod_size']
    msg = disable_helper(pod_name, pod_size, upper_bound)
    requests.post(proxy_url[pod_name]+'/cloud/elasticity/size/'+pod_name+'/0/' + str(upper_bound))

    return jsonify({'response' : pod_name+" disabled " + msg})



def disable_helper(pod_name, pod_size, upper_bound):
    while(int(pod_size) > int(upper_bound)): #if pod_size > upper_bound, remove pods
        node_datas = json.loads(requests.get(proxy_url[pod_name] + '/cloudproxy/allPods/all').text)
        node_datas.pop(0)
        node_to_remove = random.choice(node_datas)['node']
        ####really really tired
        ####really really tired

        response = requests.delete(proxy_url[pod_name] + '/cloudproxy/nodes/' + node_to_remove)
        data = response.json()
    
        if data["result"] == "success" and data["status"] == "ONLINE":
            disable_cmd = "echo 'experimental-mode on; set server " + pod_name.split('_')[0] + "-servers/" + data['name'] + ' state maint ' + "' | sudo socat stdio /run/haproxy/admin.sock"
            subprocess.run(disable_cmd, shell = True, check = True)
        
            del_cmd = "echo 'experimental-mode on; del server " + pod_name.split('_')[0] + "-servers/" + data['name'] + "' | sudo socat stdio /run/haproxy/admin.sock"
            subprocess.run(del_cmd, shell = True, check = True)

        ####really really tired
        ####really really tired
        pod_size = pod_size - 1   
    return "the size of " + str(pod_name) + " is " + str(pod_size)
        


@app.route('/cloud/elasticity/lower/<pod_name>/<value>')
def cloud_elasticity_lower(pod_name,value):
    elasticity_status[pod_name]['lower'] = value
    return jsonify({'response' : pod_name+" lower value set to" + value})
@app.route('/cloud/elasticity/upper/<pod_name>/<value>')
def cloud_elasticity_upper(pod_name,value):
    elasticity_status[pod_name]['upper'] = value
    return jsonify({'response' : pod_name+" upper value set to" + value})
if __name__ == '__main__':
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    monitor_thread1 = Thread(target=usage_monitor_manager1)
    monitor_thread1.start()
    monitor_thread2 = Thread(target=usage_monitor_manager2)
    monitor_thread2.start()
    # monitor_thread3 = Thread(target=usage_monitor_manager3)
    # monitor_thread3.start()
    app.run(debug=True, host='0.0.0.0', port=5000)