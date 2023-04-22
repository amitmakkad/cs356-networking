import re
import json


buffer_files = {
    "GRAPH": "input/graph.txt",
    "REQUEST": "input/request.json",
    "RESPONSE": "input/response.json"
}


def clear_log():
    for file_name in buffer_files.values():
        print(file_name)
        with open(file_name, "w+") as f:
            # try:
            #     json.dump({}, f)
            # except:
            #     pass
            f.read()

def get_regex_num(str):
        pattern = r"\d+"
        match = re.search(pattern, str)
        if match:
            number = int(match.group())
            return number
        else:
            print("No match found")

def swap(s1, s2):
    if s1>s2:
        return s2,s1
    return s1,s2

def file_write_line(f, line):
    for data in line:
        f.write(str(data))
        f.write(" ")
    f.write("\n")

def input_data(self):

    f = open("input/topology.txt", "r")
    
    self.num_hosts, self.num_switches = list(map(int,f.readline().split(' ')))

    for i in range(self.num_hosts):
        list(map(int,f.readline().split(' ')))

    link = f.readline()

    while link:
        
        s1, s2, bw, delay = list(map(int,link.split(' ')))
        s1,s2 = swap(s1,s2)
        self.bandwidth[(s1,s2)], self.delay[(s1,s2)] = bw, delay

        link = f.readline()
        
    f.close()


def get_host_addresses(host):
    
    return  {
        "MAC": host.mac,
        "IPV4": "10.0.0." + str(str(host.mac).split(":")[-1][-1])
    }