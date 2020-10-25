import json
import bankLedger
import node_core

nodeID = 'aaaaaaaa'
requestID_index = 10


bledger = bankLedger.bankLedger()
node_core = node_core.node_core(nodeID)

print("Create a new ledger.   ID=%s" % bledger.get_ledgerID())
print(bledger.get_ledger())

#窓口ノードがスマホ等から新しいコマンドメッセージを受信
#receive a new request from end-terminal
ReceivedPackets = []
newTransactionRequest = {'type':'newRequest','payload':[{'type':'initialBalance','AccountID':'A0000001','balance':1000}]}
ReceivedPackets.append(newTransactionRequest)
newTransactionRequest = {'type':'newRequest','payload':[{'type':'pointTransfer','from':'B0000002','to':'C0000003','amount':100}]}
ReceivedPackets.append(newTransactionRequest)
print("\nNode <%s>  Received a new reuest from an end terminal:   %s" % (nodeID,ReceivedPackets))


print('Processing new requests %s\n' % ReceivedPackets)
transmit_packets = node_core.distribute_new_requests(ReceivedPackets)
print('Transmit new requests to other nodes: \n%s' % transmit_packets)
print("Status \n%s" % json.dumps(node_core.get_request_status(),indent=2))
print()

#他のノード群からコマンドメッセージを受信
#Receive new requests from nodes
ReceivedPackets = [] #メッセージ受信バッファ
for transmit_packet in transmit_packets:
    ReceivedPackets.append(transmit_packet) #loopback（自分で送ったメッセージを受信したとする）
#for transmit_packet in transmit_packets:
#    ReceivedPackets.append(transmit_packet) #loopback（自分で送ったメッセージを受信したとする）
print("Received new requests from other nodes:\n%s\n" % ReceivedPackets)

transmit_packets = node_core.generate_new_block(ReceivedPackets)
print("\nDistribute new blocks to other nodes:")
for packet in transmit_packets:
    print("    %s" % packet)
print("Status \n%s" % json.dumps(node_core.get_request_status(),indent=2))
print("\n\nExchanging....\n\n")


ReceivedPackets = []
for packet in transmit_packets:
    ReceivedPackets.append(packet) #Loop Back

node_core.store_new_block_candidates(ReceivedPackets)
status = node_core.get_request_status()
print("Status \n%s\n\n\n" % status)

receivedResults = []
#Wait for other nodes
#Receive candidates from other nodes
receivedNewSegments = {}
approvedTransactionsList = {}
for requestID in status: #他ノードを含む送信パケット群
    print(requestID)
    status_for_rid = status[requestID]
    print("status of RID%s\n%s" % (requestID,status_for_rid))
    receivedNewSegments[requestID] = []
    if ((status_for_rid['status'] == 'receiving') and (status_for_rid['elapsedTime'] == 0)):
        responses = status_for_rid['response']
        for accid in responses:
            print(accid)
            for response in responses[accid]:
                print("response related Acc %s \n%s" % (accid,response))
                receivedNewSegment = {'sender':response['sender'],
                                   'newTransaction':response['newTransaction'],'hash':response['hash'],
                                      'AccountID':accid}
                receivedNewSegments[requestID].append(receivedNewSegment)

    responses = receivedNewSegments[requestID]
    rsp_for_rid = {} #requestID に帯する各ノードが作成した新リングの候補

# 多数決のために送信元ノードごとのハッシュ値のヒストグラムを作成
# Majority Voting Logic
    print("\nMajority Voting for %s" % requestID)
    hash_hist = {}
    print(responses)
    transaction_table = {}
    for response in responses:
        print(response)
        sender = response['sender']
        transactions = response['newTransaction']
        account = response['AccountID']
        hash = response['hash']
        transaction_table[hash] = transactions
        if account not in hash_hist:
            hash_hist[account] = {}
        print(hash_hist)
        if hash not in hash_hist[account]:
            hash_hist[account][hash] = 1
        else:
            hash_hist[account][hash] += 1
    print(hash_hist)

    selected_hash = {}
    selected_transactions = {}
    for acc in hash_hist:
        print(acc)
        max_count = 0
        total_count = 0
        selected_hash[acc] = {}
        selected_transactions[acc] = {}
        for hash in hash_hist[acc]:
            print(hash)
            count = hash_hist[acc][hash] #hash値ごとの個数
            total_count += count

            if (max_count < count):
                max_count = count #最大頻度の個数
                selected_hash[acc] = hash #最大頻度のhash
                selected_transactions[acc] = transaction_table[hash]
    print(selected_hash)
    print(selected_transactions)

    print("")
    selected_segment = {}
    for acc in selected_hash:
        selected_segment[acc] = {'newTransaction':selected_transactions[acc],'hash':selected_hash[acc]}
    approvedTransactionsList[requestID] = selected_segment

print("Approved Segments %s\n" % approvedTransactionsList)

for rid in approvedTransactionsList:
    approvedSegment = approvedTransactionsList[rid] #合意済み新リング候補
    print(approvedSegment)
    for acc in approvedSegment:
        newSegment = approvedSegment[acc]['newTransaction']
        hash = approvedSegment[acc]['hash']
        print("Approved new segment = %s  hash = %s" % (newSegment,hash))
        print(bledger.caliculate_hash(newSegment))
        #合意した　新リング候補を台帳に追加try
        print("Adding a new segment to the ledger")


        added = node_core.append_new_segment(newSegment,hash)
        if (added):
            print("Success")
        else:
            print("Failed to add the new segment")


print(node_core.get_request_status())