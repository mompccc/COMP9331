def Graph(textname):
    line = []
    times = []
    graph = {}
    with open (textname) as file:
        lines = file.readlines()
        for i in range(len(lines)):
            line.append(lines[i].split())
        for k in range(len(line)):
            times.append(line[k][0])
            times.append(line[k][1])
    num = len(set(times))
    for i in range (num):
        graph[i]={}
        for j in range(num):
            graph[i].update({j:[0,0]})
    for j in range(len(line)):
        graph[int(ord(line[j][0])) - 65][int(ord(line[j][1])) - 65][0] = int(line[j][2])
        graph[int(ord(line[j][0])) - 65][int(ord(line[j][1])) - 65][1] = int(line[j][3])
    return graph
print(Graph("1.txt"))

