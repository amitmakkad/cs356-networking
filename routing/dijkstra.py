import heapq
from typing import *

import heapq


def dijkstra(src, bw_query, adj, links):
    # Initialize distances and paths
    distances = {vertex: float("inf") for vertex in adj}
    distances[src] = 0
    paths = {vertex: [] for vertex in adj}
    paths[src] = [src]

    # Initialize heap priority queue
    pq = [(0, src)]

    # Run Dijkstra's algorithm
    while pq:
        (dist, curr_vertex) = heapq.heappop(pq)

        # Skip visited vertices
        if dist > distances[curr_vertex]:
            continue

        # Update distances and paths for neighboring vertices
        for neighbor in adj[curr_vertex]:
            if ((curr_vertex, neighbor) not in links) or (
                links[(curr_vertex, neighbor)][2] < bw_query
            ):
                continue
            weight = links[(curr_vertex, neighbor)][4]
            new_dist = dist + weight
            if new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                paths[neighbor] = paths[curr_vertex] + [neighbor]
                heapq.heappush(pq, (new_dist, neighbor))

    # Return shortest paths and distances
    return distances, paths

def get_output(dst_path, links,n_switch):
    rules = {(dst_path[0]-n_switch, dst_path[-1]-n_switch):[]}
    ports = []
    for i in range(len(dst_path) - 1):
        s1, s2 = dst_path[i], dst_path[i + 1]
        ports.append(links[(s1, s2)][0])
        ports.append(links[(s1, s2)][1])
    ports = ports[1 :-1]
    cnt=0
    for i in range(len(dst_path) - 2):
        s = dst_path[i + 1]
        port1=ports[cnt]
        port2=ports[cnt+1]
        cnt+=2
        rules[(dst_path[0]-n_switch, dst_path[-1]-n_switch)].append((s, port1, port2))
    return rules


def dijkstra_all_pair(adj,links,n_host,n_switch,n_switch_link):
    rules={}
    for i in range(1+n_switch,1+n_switch+n_host):
        dist,path = dijkstra(i,-1,adj,links)
        
        for key, value in path.items():
            if(key <= n_switch or key==i):
                continue
            
            rules.update(get_output(value, links,n_switch))
    return rules

def update_links(links, dst_path, bw_query):
    print(dst_path)
    for itr in range(0,len(dst_path)-1):
        i,j = dst_path[itr], dst_path[itr+1]
        [bw, delay, cost] = links[(i,j)][2:]
        bw -= bw_query
        cost = 0
        links[(i,j)][2], links[(i,j)][4] = bw, cost
        links[(j,i)][2], links[(j,i)][4] = bw, cost
    return links