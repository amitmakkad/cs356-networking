import json
import ast
from .dijkstra import dijkstra, get_output, dijkstra_all_pair

def get_cost(bw, delay):

    if bw == 0:
        return 10000000
    
    return (delay+1)/(bw+1) 


    return delay - bw


# 4 7
# 1 1
# 2 5
# 3 6
# 4 7
# 1 2 5 10
# 1 3 5 10
# 2 4 5 10
# 3 4 5 10
# 4 5 5 10
# 4 7 5 10
# 5 6 5 10
# 5 7 5 10

def find_optimal_paths():

    try:
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
    
    except Exception as E:
        print("routing", E)
        return -1
    