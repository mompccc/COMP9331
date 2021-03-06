#!/usr/bin/python3.5
from sys import argv

def Graph(textname):  # create topology graph
    line = []
    times = []
    graph = {}
    all_seg = {}
    D = {}
    with open(textname) as file:
        lines = file.readlines()
        for i in range(len(lines)):
            line.append(lines[i].split())
        for k in range(len(line)):
            first_node = line[k][0]
            second_node = line[k][1]
            carry = int(line[k][3])
            delay = int(line[k][2])
            times.append(first_node)
            times.append(second_node)
            if first_node < second_node:
                all_seg[first_node+"-"+ second_node] = [0, carry, delay]
                D[first_node + "-" + second_node] = []
            else:
                all_seg[second_node + "-" + first_node] = [0, carry, delay]
                D[second_node + "-" + first_node] = []
    num = len(set(times))
    for i in range(num):
        graph[i]={}
        for j in range(num):
            graph[i].update({j:[0,0]})
    for j in range(len(line)):
        graph[ord(line[j][0]) - 65][ord(line[j][1]) - 65][0] = int(line[j][2])
        graph[ord(line[j][0]) - 65][ord(line[j][1]) - 65][1] = int(line[j][3])
        graph[ord(line[j][1]) - 65][ord(line[j][0]) - 65][0] = int(line[j][2])
        graph[ord(line[j][1]) - 65][ord(line[j][0]) - 65][1] = int(line[j][3])
    return graph, all_seg, D

def search(G, start, end, IN):  # Dijkstra's algorithm
    dist = []
    pred = []
    path = []
    E = end
    pred = [-1 for i in range(0, len(G))]
    dist = [float('inf') for i in range(0, len(G))]
    dist[start] = 0
    vSet = {i for i in range(0, len(G))}
    while vSet:
        min = float('inf')
        s = 0
        for i in range(0, len(G)):
            if i in vSet:
                if dist[i] < min:
                    min = dist[i]
                    s = i
        for t in range(0, len(G)):
            if sum(G[s][t]) != 0:
                if s < t:
                    temp2 = chr(s+65)+"-"+chr(t+65)
                else:
                    temp2 = chr(t + 65) + "-" + chr(s + 65)
                if IN == 'SHP':  # case of SHP, set weight to 1
                    rate = 1
                elif IN == 'SDP':  # case of SDP, set weight to delay
                    rate = G[s][t][0]
                else:  # case of LLP, set weight to the radio of current load/max load
                    rate = all_segment[temp2][0]/all_segment[temp2][1]
                if dist[s] + rate < dist[t]:
                    dist[t] = dist[s] + rate
                    pred[t] = s
        vSet.remove(s)
    while pred[E] != -1:
        path.append(E)
        E = pred[E]
    path.append(E)
    path.reverse()
    point = 0
    segment = []
    for i in range(1, len(path)):
        if path[point] < path[i]:
            temp1 = chr(path[point]+65) + "-" + chr(path[i]+65)
        else:
            temp1 = chr(path[i] + 65) + "-" + chr(path[point] + 65)
        segment.append(temp1)
        point = i
    return dist, path, segment

def Work(line, G):
    global count
    global all_segment
    global hop
    global total_delay
    global D
    key = 1
    temp = line.split()
    start_time = float(temp[0])
    start_node = ord(temp[1]) - 65
    end_node = ord(temp[2]) - 65
    stay_time = float(temp[3])
    end_time = start_time + stay_time
    dist, path, segment = search(G, start_node, end_node, TYPE)  # segment contains linked segments from start_code to end_node
    for seg in segment:
        if all_segment[seg][0] >= all_segment[seg][1]:
            key = 0
    if key:
        print("Routed path: {}".format(segment))
        for E in D:
            for i in D[E]:
                if start_time > i:
                    D[E].remove(i)
                    all_segment[E][0] -= 1
        for seg in segment:
            D[seg].append(end_time)
            all_segment[seg][0] += 1
            total_delay += all_segment[seg][2]
        hop += len(segment)
    else:
        print("Blocked path: {}".format(segment))
        count += 1

program, circuit, TYPE, file1, file2 = argv
G, all_segment, D = Graph(file1)  # all_segment contains all connection between each two nodes, has value of current_load, max_load, delay
count = 0
hop = 0
total_delay = 0


with open(file2) as file:
    lines = file.readlines()
    total_number = len(lines)
    for line in lines:
        Work(line, G)

print("--------------------- {} ---------------------".format(TYPE))
print("total number of virtual circuit requests: {}".format(total_number))
print("number of successfully routed requests: {}".format(total_number-count))
print("percentage of routed request: %2.2f" % ((1 - count/total_number)*100))
print("number of blocked requests: %d" % count)
print("percentage of blocked request: %2.2f" % ((count/total_number)*100))
print("average number of hops per circuit: %2.2f" % (hop/(total_number-count)))
print("average cumulative propagation delay per circuit: %2.2f" % (total_delay/(total_number-count)))
