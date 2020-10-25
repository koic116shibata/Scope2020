import random
import node_core_M

nodes = []

#初期ノード作成　テスト用

i= 0
nodeID = ("node%04d" % i)
node = node_core_M.node_core(nodeID)
node.create_new_ledger()
node.create_new_ledger()
node.set_initial_account(0,'A0000001',1000)
node.set_initial_account(1,'B0000002',2000)
node.set_initial_account(0,'C0000003',3000)
ledgerlist = node.get_ledger_ID_list()
ledger1 = node.get_ledger_contents(ledgerlist[0])
ledger2 = node.get_ledger_contents(ledgerlist[1])
nodes.append(node)

print(ledger1)
print(ledger2)

#ノードをN個作成　node0の台帳野中身を乱数で配置

for i in range(1,5):
    nodeID = ("node%04d" % i)
    print("nodeID = %s" % nodeID)
    node = node_core_M.node_core(nodeID)
    i = 0
    if (random.randrange(0, 256)) > 180:
        node.create_clone_ledger(ledger1)
        ledgerC = node.get_ledger_contents(ledgerlist[i])
        i += 1
        print(ledgerC)
    if (random.randrange(0, 256)) > 100:
        node.create_clone_ledger(ledger2)
        ledgerC = node.get_ledger_contents(ledgerlist[i])
        i += 1
        print(ledgerC)
    nodes.append(node)

#ノード0　が窓口ノードとしてスマホ等からリクエストを受け取りブロードキャスト

ReceivedPackets = []
newTransactionRequest = {'type':'newRequest','payload':[{'type':'pointTransfer','from':'B0000002','to':'C0000003','amount':500}]}
ReceivedPackets.append(newTransactionRequest)
print("\nNode [%s]  Received a new reuest from an end terminal:   %s\n" % (nodeID,ReceivedPackets))

transmit_packets = nodes[0].distribute_new_requests(ReceivedPackets)
print('Transmit new requests to other nodes: \n%s\n' % transmit_packets)


#ブロードキャストされたリクエストを全ノードが受け取り、次の台帳断片ブロックを作成して、ブロードキャスト

exchange_packet = []
for node in nodes:
    ReceivedPackets = []
    for packet in transmit_packets:
        ReceivedPackets.append(packet)
    transmit_packets2 = node.generate_new_block(ReceivedPackets)
    nodeID = node.nodeID
    print("nodeID %s" % nodeID)
    print("Distribute new blocks to other nodes:%s" % transmit_packets2)
    print("Status %s" % node.get_request_status())
    print("")
    for packet in transmit_packets2:
        exchange_packet.append(packet)

print("Exchange...")
for packet in exchange_packet:
    print(packet)
print("")

#全ノードからブロードキャストされた台帳断片ブロックを、全ノードが受け取り多数決等で判定し、OKなら台帳を更新
for time  in range(0,12):
    for node in nodes:
        node.proceed_time()


    for node in nodes:
        print("\nnodeID %s" % nodeID)
        ReceivedPackets = []
        for packet in exchange_packet:
            ReceivedPackets.append(packet)
        node.store_new_block_candidates(ReceivedPackets)
        status = node.get_request_status()
        nodeID = node.nodeID
        print("Status %s" % status)
        account_list = node.get_account_list()
    #    print("account list: %s" % account_list)

        for account in account_list:
            print("balance %s  %s" % (account, node.get_balance(account)))
    print("\n\n")

#    ledgerA = node.get_ledger_contents(ledgerlist[0])
#    ledgerB = node.get_ledger_contents(ledgerlist[1])
#    print(ledgerA)
#    print(ledgerB)

for node in nodes:
    id = node.nodeID
    status = node.get_request_status()
    str = ('%s' % id)
    if 'node0000_0000' in status:
        result = status['node0000_0000']['status']
        votingStst = {}
        if 'voting' in status['node0000_0000']:
            votingStst = status['node0000_0000']['voting']
        str = str + (" %s %s" % (result,votingStst))
    print(str)
