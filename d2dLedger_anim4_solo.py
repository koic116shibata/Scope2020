import networkx as nx
import matplotlib.patches as pt
import matplotlib.pyplot as plt
import random
from matplotlib import animation
import d2dLedgerNode
import copy

Animation = True
ShowPict = False

if Animation:
    mp4writer = animation.FFMpegWriter(fps=4, metadata=dict(artist='kshibata'), bitrate=4000)

random.seed(0)

width = 1920
height = 1080
timeLength = 600
node_count = 50
maxrange = 384
start_time = 1

ComErrorRatio = 40  # %
dataErrorRatio = 40  # %

ledgerRatio = 60

waitTime = 8

testRequestList = []
for i in range(0,10):
    testRequests = {'time':(i*54)+2,'node':random.randrange(0,node_count),'request':[{'type':'newRequest','payload':[{'type':'pointTransfer','from':'B0000002','to':'C0000003','amount':500}]}]}
    testRequestList.append(testRequests)
    testRequests = {'time':(i*54)+20,'node':random.randrange(0,node_count),'request':[{'type':'newRequest','payload':[{'type':'pointTransfer','from':'C0000003','to':'A0000001','amount':500}]}]}
    testRequestList.append(testRequests)
    testRequests = {'time':(i*54)+38,'node':random.randrange(0,node_count),'request':[{'type':'newRequest','payload':[{'type':'pointTransfer','from':'A0000001','to':'B0000002','amount':500}]}]}
    testRequestList.append(testRequests)

reqIdx = []
reqIdx.append(0)
nextRequest = testRequestList[0]

requestLog = []

#
G = nx.DiGraph()
G2 = nx.DiGraph()
G2.add_node(0,Position=(0,0))
G2.add_node(1,Position=(1920,0))
G2.add_node(2,Position=(0,1080))
G2.add_node(3,Position=(1920,1080))

statistics = []

def nodes_process(tt):

    print("\nTime=%d" % tt)

    idx = reqIdx[0]


    req_packet = []
    nextRequest = testRequestList[idx]
    start_time = nextRequest['time']
    if (tt == start_time):
        testRequest = nextRequest['request']
        g_node = nextRequest['node']
        if ((len(testRequestList) - 1) > idx):
            reqIdx[0] = idx + 1

        rids = nodes[g_node].receive_new_request(testRequest)

        for rid in rids:
            requestLog.append(rid)

        requestID = requestLog[-1]

        for packet in nodes[g_node].send_buf:
            print('Node %s transmit new command to other nodes %s' % (nodes[g_node].id,packet))
            req_packet.append(packet)

    for node in nodes:
        node.proceed_time()

# Receive Packets
    for node in nodes:
        node.clear_input_buf()
        inputPackets = []
        for packet in on_the_air:
            if (random.randrange(0, 100)) > ComErrorRatio:  #Communication Error
                if (random.randrange(0, 100)) < dataErrorRatio:  # Data Error
                    if 'payload' in packet:
                        errpacket = copy.copy(packet)
                        errpacketPayload = copy.copy(errpacket['payload'])
                        if 'contents' in errpacketPayload:
                            errpacketContents = copy.copy(errpacketPayload['contents'])
                            if errpacketContents['messageType'] == 'newSegment':
                                errTransactions = []
                                for transaction in errpacketContents['newTransaction']:
                                    errTransactions.append(copy.copy(transaction))
                                errTransactions[0]['balance'] = random.randrange(0, 1000)
                                errpacketContents['newTransaction'] = errTransactions
                            errpacketPayload['contents'] = errpacketContents
                        errpacket['payload'] = errpacketPayload
                        inputPackets.append(errpacket)
                else:
                    inputPackets.append(packet)
#       if len(inputPackets) > 0:
#            print('Node %s receive %d packets from other nodes' % (node.id, len(inputPackets)))
#        for packet in inputPackets:
#            print('Node %s receive packets from other nodes %s' % (node.id,packet))

        node.put_data(inputPackets)

#        if len(node.send_buf) > 0:
#            print('Node %s Distribute %d new packet to other nodes.' % (node.id,len(node.send_buf)))
#            for packet in node.send_buf:
#                print('          %s' % packet)
#        node_status = node.get_status(requestID)
#        if len(node_status) > 0:
#            print('  Node %s Status of %s:%s' % (node.id,requestID,node_status))




# Transmit Packets
    on_the_air.clear()
    for node in nodes:
        for packet in node.send_buf:
            on_the_air.append(packet)
        node.send_buf.clear()
    for packet in req_packet:
        on_the_air.append(packet)


    accountlist = nodes[0].get_account_list()
    strr = ("%s:  " % (nodes[0].id))
    for acc in accountlist:
        balance = nodes[0].get_balance(acc)
        strr += ("%s  %s      " % (acc,balance))
    print(strr)


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
    successCount = 0
    failCount = 0
    waitingCount = 0
    totalCount = 0
    for gnode in G.nodes():
        color = '#C0C0C0'
        for node in nodes:
            if (node.id == gnode):
                lastReqID = ''
                if (len(requestLog) > 0):
                    lastReqID = requestLog[-1]
                status = node.get_status_digest(lastReqID)
                totalCount += 1
#                print("%s Status %s" % (node.id,status))
                total = 0
                strr = ''
                if (status == 'receiving'):
                    counts = node.get_status_response_count(lastReqID)
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
                voting = node.get_status_response_stat(lastReqID)
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
newnode.set_initial_account(0,'B0000002',2000)
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
    if (random.randrange(0, 100)) < ledgerRatio:
        newnode.create_clone_ledger(ledger1)
        ledgerC = newnode.get_ledger_contents(ledgerlist[j])
        j += 1
        newnode.add_ledger_name("L0")
        print(ledgerC)
    if (random.randrange(0, 100)) < 0:
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

requestID = ''

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
        if ShowPict:
            plt.show()

for stat in statistics:
    print(stat)

for log in requestLog:
    requestID = log
#    print('RequestID = %s' % requestID)

    s = 0
    t = 0
    f = 0

    for node in nodes:
        stats = node.get_status(requestID)
        if len(stats) > 0:
            if ('status' in stats) and ('voting' in stats) and ('hashList' in stats):
    #            print("%s Status: %s   voting %s   histgram %s" % (node.id,stats['status'],stats['voting'],stats['hashList']))
                if stats['status'] == 'Success':
                    s += 1
                    t += 1
                if stats['status'] == 'Failed':
                    f += 1
                    t += 1



#    error = 0
#    t2 = 0
#    for node in nodes:
#        accountlist = node.get_account_list()
#        strr = ("%s:  " % (node.id))
#        for acc in accountlist:
#            balance = node.get_balance(acc)
#            strr += ("%s  %s      " % (acc,balance))
#            stats = node.get_status('N000_0000')
#            if 'status' in stats:
#                if stats['status'] == 'Success':
#                    t2 += 1
#                    if (acc == 'B0000002') and (balance != 1500):
#                        error += 1
#                    if (acc == 'C0000003') and (balance != 3500):
#                        error += 1
    #    print(strr)

    if (t > 0):
        print("RequestID:%s  Success Ratio = %f   Fail Ratio = %f\n" % (requestID,(s*100)/t,(f*100)/t))
    else:
        print("t=0")

#    if (t2 > 0):
#        print("Error ratio = %f" % ((error * 100)/t2))

#    print("Participatant nodes %d  / Total %d" % (t,node_count))
