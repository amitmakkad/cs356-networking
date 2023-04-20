import json
import ast
from .dijkstra import dijkstra, get_output, dijkstra_all_pair

def get_cost(bw, delay):
    return delay - bw

def shortest_path():

    with open("input/graph.txt", "r") as f:
        data = f.read().strip()

    mylist = data.split("\n")
    mylist = [list(map(int, x.strip().split(" "))) for x in mylist]

    is_query = True
    if len(mylist[0])==1:
        is_query = False
    else:
        src, dst, bw_query = mylist[0]

    n_host, n_switch = mylist[1]
    [n_switch_link] = mylist[2]

    switch_links = mylist[3 : 3 + n_switch_link]
    host_links = mylist[-n_host:]
    adj = {}

    links = {}
    for link in switch_links:
        s1, p1, s2, p2, bw, delay = link
        cost = get_cost(bw, delay)
        links[(s1, s2)] = [p1, p2, bw, delay, cost]
        links[(s2, s1)] = [p2, p1, bw, delay, cost]
        
        if s1 not in adj:
            adj[s1] = []
        if s2 not in adj:
            adj[s2] = []
        adj[s1].append(s2)
        adj[s2].append(s1)

    for link in host_links:
        h1, s2, p2 = link
        s1 = h1 + n_switch
        bw, delay, cost = 1000000000, 0, 0
        links[(s1, s2)] = [1, p2, bw, delay, cost]
        links[(s2, s1)] = [p2, 1, bw, delay, cost]
        if s1 not in adj:
            adj[s1] = []
        if s2 not in adj:
            adj[s2] = []
        adj[s1].append(s2)
        adj[s2].append(s1)

    if is_query:

        src += n_switch
        dst += n_switch

        _, path = dijkstra(src, bw_query, adj, links)
        dst_path = path[dst]
        src_dst = get_output(dst_path, links,n_switch)

        _, path = dijkstra(dst, bw_query, adj, links)
        dst_path = path[src]
        dst_src = get_output(dst_path, links,n_switch)

        res = src_dst | dst_src
        return res

    else:
        all_rules = dijkstra_all_pair(adj,links,n_host,n_switch,n_switch_link)
        return all_rules
    
def find_shortest_paths():

    try:

        optimal_paths = shortest_path()
        init_call = False

        with open("input/paths.json", "r") as file:
            try:
                res = json.loads(file.read())
            except:
                init_call = True

        if init_call:

            res = {
                "updated": True,
                "accept_connections": False,
                "optimal_paths": optimal_paths
            }

        elif res["accept_connections"] == False:

            res = {
                "updated": True,
                "accept_connections": True,
                "optimal_paths": optimal_paths
            }

        else:
            res["optimal_paths"] = {ast.literal_eval(k): ast.literal_eval(v) for k, v in res["optimal_paths"].items()}
            res["optimal_paths"] = res["optimal_paths"] | optimal_paths


        res["updated"] = True
        res["optimal_paths"] = {str(k): str(v) for k, v in res["optimal_paths"].items()}

        with open("input/paths.json", "w") as file:
            json.dump(res, file, indent=4)

        return optimal_paths
    
    except Exception as E:
        print("find_shortest_paths", E)
        return -1

def get_shortest_paths():

    try:
        with open("input/paths.json", "r") as file:
            res = json.loads(file.read())

        if (res is None) or res["updated"] == False:
            print("Returning -1")
            return -1
    
        res["optimal_paths"] = {ast.literal_eval(k): ast.literal_eval(v) for k, v in res["optimal_paths"].items()}
        optimal_paths = res["optimal_paths"]

        res["updated"] = False
        res["optimal_paths"] = {str(k): str(v) for k, v in res["optimal_paths"].items()}

        with open("input/paths.json", "w+") as file:
            json.dump(res, file, indent=4)

        return optimal_paths
            
    except Exception as E:
        print("get_shortest_paths", E)
        return -1

