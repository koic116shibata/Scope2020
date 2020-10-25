import node_core_M

nodeID = 'aaaaaaaa'
requestID_index = 10

node_core = node_core.node_core(nodeID)
node_core.create_new_ledger()

node_core.set_initial_account('A0000001',1000)
node_core.set_initial_account('B0000002',400)
node_core.set_initial_account('C0000003',3000)

#窓口ノードがスマホ等から新しいコマンドメッセージを受信
#receive a new request from end-terminal
ReceivedPackets = []
newTransactionRequest = {'type':'newRequest','payload':[{'type':'pointTransfer','from':'B0000002','to':'C0000003','amount':500}]}
ReceivedPackets.append(newTransactionRequest)
print("\nNode [%s]  Received a new reuest from an end terminal:   %s\n" % (nodeID,ReceivedPackets))

transmit_packets = node_core.distribute_new_requests(ReceivedPackets)
print('Transmit new requests to other nodes: \n%s\n' % transmit_packets)
#print("Status \n%s" % json.dumps(node_core.get_request_status()- ,indent=2))
#print()

#他のノード群からコマンドメッセージを受信
#Receive new requests from nodes
#ReceivedPackets = [] #メッセージ受信バッファ
for transmit_packet in transmit_packets:
    ReceivedPackets.append(transmit_packet) #loopback（自分で送ったメッセージを受信したとする）
print("Received new requests from other nodes:\n%s\n" % ReceivedPackets)

transmit_packets = node_core.generate_new_block(ReceivedPackets)
print("\nDistribute new blocks to other nodes:\n %s" % transmit_packets)
print("Status \n%s" % node_core.get_request_status())
print("\n\nExchanging....\n\n")

for packet in transmit_packets:
    ReceivedPackets.append(packet) #Loop Back

print("Received new candidates of new segment. %s" % ReceivedPackets)
node_core.store_new_block_candidates(ReceivedPackets)
status = node_core.get_request_status()
print("Status \n%s\n\n\n" % status)

account_list = node_core.get_account_list()
print("account list: %s" % account_list)

for account in account_list:
    print("balance %s  %s" % (account,node_core.get_balance(account)))


