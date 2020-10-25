import networkx as nx
import matplotlib.pyplot as plt
import random
from matplotlib import animation
import p2pnode

Animation = True

if (Animation):
    mp4writer = animation.FFMpegWriter(fps=5, metadata=dict(artist='kshibata'), bitrate=4000)


width = 1920
height = 1080
timeLength = 30
node_count = 200
maxrange = 150
start_time = 5

nodes = []

#
G = nx.DiGraph()

def nodes_process(tt):
    if (tt == start_time):
        on_the_air.append(testpacket)

# Receive Packets
    for node in nodes:
        node.clear_input_buf()
        for packet in on_the_air:
            node.put_data(packet)

# Processing Packets
    for node in nodes:
        node.processing()

# Transmit Packets
    on_the_air.clear()
    for node in nodes:
        for packet in node.send_buf:
            on_the_air.append(packet)

#Draaw Graph
    plt.clf()
    G.clear()
    labelList = {}

    for node in nodes:
        id = node.id
        ix = node.x
        iy = node.y
        G.add_node(id,Position=(ix, iy))
        labelList.update({id:node.id})
        receive_from = node.stat_receive_from
        for id2 in receive_from:
            G.add_edge(id2,id)

    col = []
    for gnode in G.nodes():
        color = '#C0C0C0'
        for node in nodes:
            if (node.id == gnode):
                if (node.stat_received > 0):
                    color = '#FFC0C0'
                if (node.stat_just_received):
                    color = '#FF0000'
        col.append(color)

    pos = nx.get_node_attributes(G,'Position')
    nx.draw(G,pos,node_color = col, labels = labelList, node_size = 500,
            font_size=10, font_color = 'k', linewidths = 0.5)


#construct and initialize nodes
nodes = []

for i in range(0,node_count):
    ix = random.randrange(192, width-192)
    iy = random.randrange(108, height-108)
    newnode = p2pnode.node(("N%d" % i),ix,iy)
    newnode.set_receive_range(maxrange)
    nodes.append(newnode)

#for node in nodes:
#    print("ID=%s x=%d y=%d" % (node.id,node.x,node.y))



#setup
on_the_air = []

#Test packet
testpacket = {}
testpacket['sender'] = nodes[0].id
testpacket['sender_x'] = nodes[0].x
testpacket['sender_y'] = nodes[0].y
testpacket['hopcount'] = 0
payload = {}
payload['MID'] = 'TEST0'
payload['data'] = {}
testpacket['payload'] = payload

if (Animation):
    fig = plt.figure(figsize=(19.2, 10.8), dpi=100)
    anim = animation.FuncAnimation(fig, nodes_process, frames=timeLength)
    anim.save('test.mp4', writer=mp4writer)
else:
    for tt in range(0,timeLength):
        fig = plt.figure(figsize=(19.2, 10.8), dpi=100)
        nodes_process(tt)
#        print(on_the_air)
        plt.show()
