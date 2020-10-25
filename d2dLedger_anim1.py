import networkx as nx
import matplotlib.patches as pt
import matplotlib.pyplot as plt
import random
from matplotlib import animation
import d2dLedgerNode

Animation = False

if (Animation):
    mp4writer = animation.FFMpegWriter(fps=3, metadata=dict(artist='kshibata'), bitrate=4000)


width = 1920
height = 1080
timeLength = 20
node_count = 50
maxrange = 300
start_time = 1

ComErrorRatio = 20 # %
dataErrorRatio = 1 # %

waitTime = 8

testRequest = [{'type':'newRequest','payload':[{'type':'pointTransfer','from':'B0000002','to':'C0000003','amount':500}]}]

#
G = nx.DiGraph()
G2 = nx.DiGraph()
G2.add_node(0,Position=(0,0))
G2.add_node(1,Position=(1920,0))
G2.add_node(2,Position=(0,1080))
G2.add_node(3,Position=(1920,1080))

statistics = []

def nodes_process(tt):
    req_packet = []
    if (tt == start_time):
#        print(testRequest)
        nodes[0].receive_new_request(testRequest)
        for packet in nodes[0].send_buf:
#            print(packet)
            req_packet.append(packet)

    for node in nodes:
        node.proceed_time()

# Receive Packets
    for node in nodes:
        node.clear_input_buf()
        inputPackets = []
        for packet in on_the_air:
            if (random.randrange(0, 100)) > ComErrorRatio:  #Communication Error
                if (random.randrange(0, 100)) < dataErrorRatio: #Data Error
                    if 'payload' in packet:
                        if 'contents' in packet['payload']:
                            if 'newTransaction' in packet['payload']['contents']:
                                if 'balance' in packet['payload']['contents']['newTransaction'][0]:
                                    packet['payload']['contents']['newTransaction'][0]['balance'] = random.randrange(0, 1000)
                inputPackets.append(packet)
        node.put_data(inputPackets)



# Transmit Packets
    on_the_air.clear()
    for node in nodes:
        for packet in node.send_buf:
            on_the_air.append(packet)
        node.send_buf.clear()
    for packet in req_packet:
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

    requestID = 'N000_0000'
    col = []
    successCount = 0
    failCount = 0
    waitingCount = 0
    totalCount = 0
    for gnode in G.nodes():
        color = '#C0C0C0'
        for node in nodes:
            if (node.id == gnode):
                status = node.get_status_digest(requestID)
                totalCount += 1
#                print("%s Status %s" % (node.id,status))
                total = 0
                if (status == 'receiving'):
                    counts = node.get_status_response_count(requestID)
                    total = min(counts)
                    count = (min(counts) * 5) / node_count
                    color = '#D0FFD0'
                    if count > 1:
                        color = '#B0E0D4'
                    if count > 2:
                        color = '#A0C0D8'
                    if count > 3:
                        color = '#90A0DC'
                    if count > 4:
                        color = '#8098E0'
                    waitingCount += 1
                if (status == 'Success'):
                    color = '#5070F0'
                    successCount += 1
                if (status == 'Failed'):
                    color = '#101010'
                    failCount += 1
                if (status == 'NotApproved'):
                    color = '#D060D0'
                    failCount += 1
                strr = ''
                voting = node.get_status_response_stat(requestID)
                for acc in voting:
                    strr += ('\n%s' % acc)
                    for res in voting[acc]:
                        strr += (' %d' % voting[acc][res])
                ledgers = node.get_ledger_name()
                labelList.update({gnode: "%s\n%s %d%s" % (node.id,ledgers,total,strr)})
        col.append(color)
    statistics.append("Time%4d:Total %3d   Waiting %3d   Success %3d   Fail %3d" % (tt,totalCount,waitingCount,successCount,failCount))

    pos2 = nx.get_node_attributes(G2,'Position')
    nx.draw(G2,pos2,node_color = '#FFFFFF',node_size = 0)
    pos = nx.get_node_attributes(G,'Position')
    nx.draw(G,pos,node_color = col, labels = labelList, node_size = 500,
            font_size=7, font_color = 'k', linewidths = 0.5)


#construct and initialize nodes
nodes = []

ix = random.randrange(96, width - 96)
iy = random.randrange(48, height - 48)
newnode = d2dLedgerNode.node(("N%03d" % 0), ix, iy)
newnode.create_new_ledger()
newnode.create_new_ledger()
newnode.set_initial_account(0,'A0000001',1000)
newnode.set_initial_account(1,'B0000002',2000)
newnode.set_initial_account(0,'C0000003',3000)
ledgerlist = newnode.get_ledger_ID_list()
ledger1 = newnode.get_ledger_contents(ledgerlist[0])
ledger2 = newnode.get_ledger_contents(ledgerlist[1])
newnode.set_receive_range(maxrange)
newnode.set_node_wait_time(waitTime)
newnode.add_ledger_name("L0")
newnode.add_ledger_name("L1")
nodes.append(newnode)
#print(newnode.id)
#print(ledger1)
#print(ledger2)
print(newnode.get_ledger_name())

for i in range(1,node_count):
    ix = random.randrange(96, width-96)
    iy = random.randrange(48, height-48)
    newnode = d2dLedgerNode.node(("N%03d" % i),ix,iy)
    j = 0
    print(newnode.id)
    if (random.randrange(0, 256)) > 100:
        newnode.create_clone_ledger(ledger1)
        ledgerC = newnode.get_ledger_contents(ledgerlist[j])
        j += 1
        newnode.add_ledger_name("L0")
        print(ledgerC)
    if (random.randrange(0, 256)) > 100:
        newnode.create_clone_ledger(ledger2)
        ledgerC = newnode.get_ledger_contents(ledgerlist[j])
        j += 1
        newnode.add_ledger_name("L1")
        print(ledgerC)

    newnode.set_receive_range(maxrange)
    newnode.set_node_wait_time(waitTime)
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

print("Start")

if (Animation):
    fig = plt.figure(figsize=(19.2, 10.8), dpi=100)
    axes = plt.axes()
    r = pt.Rectangle(xy=(0, 0), width=192, height=108, ec='#000000', fill=False)
    axes.add_patch(r)
    plt.axis('scaled')
    anim = animation.FuncAnimation(fig, nodes_process, frames=timeLength)
    anim.save('test.mp4', writer=mp4writer)
else:
    for tt in range(0,timeLength):
        fig = plt.figure(figsize=(19.2, 10.8), dpi=100)
        nodes_process(tt)
#        print(on_the_air)
        plt.show()

for stat in statistics:
    print(stat)