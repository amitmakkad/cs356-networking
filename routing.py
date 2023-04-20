import json
import ast

def shortest_path():

    f = open("input/graph.txt","r")

    query = (f.readline().strip().split(' '))

    # if len(query)!=1:
    #     return dict({
    #         (1,2) : [(1,1,2),(2,2,1)],
    #         (1,3) : [(1,1,3),(3,2,1)],
    #         (2,3) : [(2,1,3),(3,3,1)],

    #         (2,1) : [(2,1,2),(1,2,1)],
    #         (3,1) : [(3,1,2),(1,3,1)],
    #         (3,2) : [(3,1,3),(2,3,1)]
    #     })

    return dict({
            (1,2) : [(1,1,2),(2,2,1)],
            (1,3) : [(1,1,2),(2,2,3),(3,3,1)],
            (2,3) : [(2,1,3),(3,3,1)],

            (2,1) : [(2,1,2),(1,2,1)],
            (3,1) : [(3,1,3),(2,3,2),(1,2,1)],
            (3,2) : [(3,1,3),(2,3,1)]
        })

def find_shortest_paths():

    optimal_paths = shortest_path()

    res = {
        "updated": True,
        "optimal_paths": optimal_paths
    }

    res["optimal_paths"] = {str(k): str(v) for k, v in res["optimal_paths"].items()}

    with open("input/paths.json", "w") as file:
        json.dump(res, file, indent=4)

    return optimal_paths
    


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
        print(E)
        return -1

