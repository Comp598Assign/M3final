import subprocess
import docker
from flask import Flask, jsonify, request
import os.path
import json

app = Flask(__name__)
global_list = []
nodes = []
pods={}
jobs =[]
containers=[]
resource_manager_url=''
client = docker.from_env()
client.images.pull('ubuntu')
port = '15000'
numberofrequests = 0
maxnodes = 15
minnodes = 0
isElastic = False
class Pod:
    def __init__(self, id):
        self.id = id
        self.pod_nodes = {}
        pods[id] = self

    def __str__(self):
        return self.id
    
class Node:
    idCounter = 0
    def __init__(self, name, parentPod, port):
        self.name = name
        self.status = 'NEW'
        self.port = port
        self.parent = parentPod
        self.id = Node.idCounter
        self.container = None
        parentPod.pod_nodes[name] = self

    def __str__(self):
        return self.name
    
def get_pod(podId):
    if podId in pods:
        return pods[podId]
    return None

def rm_pod(pod):
    pods.pop(pod.id)

def rm_node(node):
    node.parent.pod_nodes.pop(node.name)
    nodes.remove(node)
    if node.container is not None:
        node.container.remove(v=True, force=True)

def get_node(node_name):
    for node in nodes:
        if node.name == node_name:
            return node
    return None

def get_available_port():
    global port
    p = port
    port = str(int(port) + 1)
    return p

def requestNodesCpu():
    nodesCpuUsage={}
    total_cpu_usage = 0.0
    for node in nodes:
        container = node.container
        if container is not None and node.status != 'NEW':
        #get container
            status = container.stats(stream=False)
            #container name
            name = container.name
            #Current and previous cpu status
            cpu_status = status["cpu_stats"]
            previous_cpu_status = status["precpu_stats"]
            #the cpu that container uses
            container_cpu_usage = float(cpu_status["cpu_usage"]["total_usage"]) - float(previous_cpu_status["cpu_usage"]["total_usage"]) 
            #the cpu that system uses
            system_cpu_usage = float(cpu_status["system_cpu_usage"]) - float(previous_cpu_status["system_cpu_usage"])
            #calculate percentage
            percentage_cpu_usage = container_cpu_usage / system_cpu_usage * 100.0
            #round the num to 2 desmal
            percentage_cpu_usage = round(percentage_cpu_usage,2)
            nodesCpuUsage[name] = percentage_cpu_usage
            total_cpu_usage += percentage_cpu_usage
            
    if len(client.containers.list()) != 0:
        total_cpu_usage = total_cpu_usage / len(client.containers.list())
        #round the num to 2 desmal
        total_cpu_usage = round(total_cpu_usage, 2)

    return {"cpu_data" : nodesCpuUsage, "total_usage": total_cpu_usage}
@app.route('/cloudproxy/initalization')
def cloud_init():
    if request.method == "GET":
        medium_pod = Pod("medium_pod")
        
        return jsonify({"response" : 'success'})

@app.route('/cloudproxy/get_nextav_node',methods=['GET'])
def cloud_getnext_node():
        if request.method == "GET":
            for node in nodes:
                if node.status == 'NEW':
                    return jsonify({"av_node":node.name})
            return jsonify({"av_node":None})
        
        
@app.route('/default_cluster/pods', methods = ['GET', 'POST'])
def pod_list():
    if request.method == "POST":
        pod_list = request.form['response_from_manager']
        print(pod_list)
        response = "List of pods printed"
        global_list.append(pod_list)
        test()
        return jsonify({"response" : response})

@app.route('/')
def test():
    return global_list[0]
@app.route('/cloud/elasticity/size/<lower_size>/<upper_size>',methods = ['POST'])
def setMaxAndMin(lower_size,upper_size):
    if request.method == "POST":
        global isElastic
        isElastic = True
        global maxnodes
        maxnodes = int(upper_size)
        global minnodes
        minnodes = int(lower_size)
        result = 'Medium Pod is now Elastic and the lower size is: '+ lower_size + ' and the upper size is: '+ upper_size
        return jsonify({"result" : result})

@app.route('/cloudproxy/<podId>/nodes/<name>', methods = ['POST'])
def node_register(podId, name):
    if request.method == "POST":
        if len(nodes) >= maxnodes:
            result = 'Pod capacity has been reached (max '+maxnodes+' nodes)'
            return jsonify({"result" : result})
        
        for node in nodes:
            if node.name == name:
                result = 'node with the same already exists'
                return jsonify({"result" : result})
            
        # container = client.containers.run('ubuntu', name = name, detach = True, tty = True)
        nodes.append(Node(name, get_pod(podId), get_available_port()))
        result = 'Added NEW node ' + name + ' under ' + podId 
        return jsonify({"result" : result})
               

@app.route('/cloudproxy/nodes/<node_name>', methods = ['DELETE'])
def node_rm(node_name):
    node = get_node(node_name)
    if node is None:
        return jsonify({"result" : "failure", "response" : "node does not exist."})
    if len(nodes) >= minnodes:
        rm_node(node)
    else:
        return jsonify({"result" : "failure", "response" : "lower size bound reached"})
    return jsonify({"result" : "success", "name" : node.name, "port" : node.port, "status" : node.status}) 
    
@app.route('/cloudproxy/<podId>/all', methods = ['GET'])
def zyjnmsl(podId):
    result=[] 
    if podId == "allPods":
        for node in nodes:
             new_dict = {}
             new_dict['node'] = node.name
             result.append( new_dict)
    else:
        pod = get_pod(podId)
        if pod is not None:
            for node in pod.pod_nodes.values():
                new_dict = {}
                new_dict['node'] = node.name
                result.append( new_dict)
        else:
            result = "failure"
    return json.dumps(result)


@app.route('/cloudproxy/<podId>/allNodes', methods = ['GET'])
def nodes_list(podId):
    result=[]
    new_dict = {}
    global numberofrequests
    new_dict['counter'] = numberofrequests
    result.append( new_dict)
    tmp = requestNodesCpu()
    nodecpu = tmp["cpu_data"]
    total = tmp["total_usage"]
    new_dict = {}
    new_dict['cpu'] = str(total)+"%"
    result.append( new_dict)
   
    if podId == "allPods":
        for node in nodes:
             new_dict = {}
             new_dict['node'] = node.name
             new_dict['status'] = node.status
             if(node.name in nodecpu):
                new_dict['usage'] = nodecpu[node.name]
             else:
                 new_dict['usage'] = "NOT Launched"
             result.append( new_dict)
    else:
        pod = get_pod(podId)
        if pod is not None:
            for node in pod.pod_nodes.values():
                new_dict = {}
                new_dict['node'] = node.name
                new_dict['status'] = node.status
                if(node.name in nodecpu):
                    new_dict['usage'] = nodecpu[node.name]
                else:
                    new_dict['usage'] = "NOT Launched"
                result.append( new_dict)
        else:
            result = "failure"
    return json.dumps(result)


@app.route('/cloudproxy/online_nodes', methods = ['GET'])
def get_online_nodes():
    if request.method == 'GET':
        node_list = list(map(lambda n : n.name, filter(lambda n : (n.status == "ONLINE"), nodes)))
        return jsonify({'node_list' : node_list})
    

@app.route('/cloudproxy/launch', defaults={'node_name' : None},methods = ['GET'])
@app.route('/cloudproxy/launch/<node_name>', methods = ['GET'])
def launch(node_name):
    if request.method == 'GET':
        global numberofrequests
        numberofrequests += 1
        if node_name is None:
            for node in nodes:
                if node.status == "NEW":
                    launch_node(node.name, node.port)
                    return jsonify ({'response' : 'success' ,'port' : node.port, 'name' : node.name, 'status' : node.status})
        else:
            node=get_node(node_name)
            if node is not None and node.status != 'ONLINE':
                launch_node(node_name, node.port)
                return jsonify ({'response' : 'success' ,'port' : node.port, 'name' : node.name, 'status' : node.status})
        return jsonify({'response' : 'failure', 'result' : 'No more available nodes'})
def launch_node(container_name, port_number):
    # [img, logs] = client.images.build (path='/', rm=True ,dockerfile = './Dockerfile' )

    for container in client.containers.list():
        if container.name == container_name:
            container.remove(v=True, force=True)

    [img, logs] = client.images.build (path='./', rm=True ,dockerfile = './Dockerfile' )
    container = client.containers.run(image=img, detach=True, name=container_name, command=['python' , 'test.py', container_name],ports={'5000/tcp' : port_number}, tty=True, cpu_quota = 50000, mem_limit = '300m')
    # container = client.containers.run(image='ubuntu', detach=True, name=container_name, command=['echo', 'hello', 'world'],ports={'5000/tcp' : port_number})
    node = get_node(container_name)
    node.container = container
    node.status = "ONLINE"
@app.route('/cloudproxy/usage', methods = ['GET'])
def usage():
    return jsonify(requestNodesCpu())

@app.route('/cloudproxy/pod_size', methods = ['GET'])
def pod_size():
    pod_size = len(nodes)
    return jsonify({"pod_size":pod_size})

if __name__ == '__main__':
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(debug=True, host='0.0.0.0', port=5000)