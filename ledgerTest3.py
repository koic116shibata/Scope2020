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
newTransactionRequest = {'type':'newRequest','payload':[{'type':'pojntTransfer','from':'B0000002','to':'C0000003','amount':100}]}
ReceivedPackets.append(newTransactionRequest)
print("\nNode <%s>  Received a new reuest from an end terminal:   %s" % (nodeID,ReceivedPackets))


print('Processing new requests %s\n' % ReceivedPackets)
transmit_packets = node_core.distribute_new_requests(ReceivedPackets)
print('Transmit new requests to other nodes: \n%s\n' % transmit_packets)

#他のノード群からコマンドメッセージを受信
#Receive new requests from nodes
ReceivedPackets = [] #メッセージ受信バッファ
for transmit_packet in transmit_packets:
    ReceivedPackets.append(transmit_packet) #loopback（自分で送ったメッセージを受信したとする）
print("Received new requests from other nodes:\n%s\n" % ReceivedPackets)


receivedCommandRequests = []
for newrequest in ReceivedPackets:
    if (newrequest['messageType'] == 'commandRequest'): #受信バッファからコマンドメッセージを抽出
        requestID = newrequest['RequestID']
        if requestID not in receivedCommandRequests: #requestIDで重複排除(多数決しても良い)
            receivedCommandRequests.append({'RequestID':requestID,'payload':newrequest['payload']})
print("Received Command Requesrs from other nodes. \n%s" % receivedCommandRequests)


transmittedPackets = []
requestStatus = {}
for receivedMessage in receivedCommandRequests:
    receivedTransactionRequests = receivedMessage['payload']
    reveivedRequestID = receivedMessage['RequestID']
    requestStatus[reveivedRequestID] = {}

    #受信したコマンドメッセージの内容が正当(残高確認等)なコマンドであることを確認
#Check received Requests
#    ledgerOperationRequests = []
    print("Checking Received Transaction Requests. ID:%s" % reveivedRequestID)

    response = bledger.get_candidate_of_new_block(receivedTransactionRequests)

    print(response)
    newSegment = response['newsegment']
    newTransaction = newSegment['newTransaction']
    newhash = newSegment['hash']
    tradability = response['tradability']
    relatedAccounts = response['relatedAccounts']
    print("\nNew Chain Candidate = \n%s" % newTransaction)
    print("hash = %s" % newhash)


# 新しいチェインの候補を送信
#Tranmit a candidate of a new segment



    transmitPacket = {}
    transmitPacket['messageType'] = 'newSegment'
    transmitPacket['RequestID'] = reveivedRequestID
    transmitPacket['sender'] = nodeID
    transmitPacket['tradability'] = tradability
    transmitPacket['relatedAccounts'] = relatedAccounts
    tradable = True
    for id in tradability:
        if tradability[id] == 'invalid':
            tradable = False
    if tradable:
        transmitPacket['newTransaction'] = newTransaction
        transmitPacket['hash'] = newhash
#    print("Transmit a candidate of new segment %s  to other nodes " % transmitPacket)
    transmittedPackets.append(transmitPacket) #送信パケット群

    for accid in relatedAccounts:
        requestStatus[reveivedRequestID][accid] = {'status':'processing','response':[],'elapsedTime':0}

print("\nTransmitting candidates of new segments %s\n" % transmittedPackets)
print("Processing Status Of Requests %s\n" % requestStatus)

receivedResults = []
#Wait for other nodes
#Receive candidates from other nodes
receivedNewRings = {}
for receivingPacket in transmittedPackets: #他ノードを含む送信パケット群
    if (receivingPacket['messageType'] == 'newSegment'):
        requestID = receivingPacket['RequestID']
        if requestID not in receivedNewRings:
            receivedNewRings[requestID] = []
        receivedNewRing = {'sender':receivingPacket['sender'],
                           'newTransaction':receivingPacket['newTransaction'],'hash':receivingPacket['hash']}
        receivedNewRings[requestID].append(receivedNewRing)
        receivedResults.append(receivedNewRings)
print("\nReceived candidates of new segment from other Nodes. \n%s\n\n" % receivedResults)

#RequestID と 発信ノードでソート
#Sort response messages
requestList2 = {}
for rID in receivedNewRings:
    responses = receivedNewRings[rID]
#    print(responses)
    rsp_for_rid = {} #requestID に帯する各ノードが作成した新リングの候補

    for rsp in responses:
#        print(rsp)
        sender = rsp['sender']
        if sender not in rsp_for_rid: #送信ノードごとに整理
            rsp_for_rid[sender] = []
        a_ring = {'newTransaction': rsp['newTransaction'],'hash': rsp['hash']}
        rsp_for_rid[sender].append(a_ring)
    print("Responses for Request ID <%s>\n   %s" % (rID,rsp_for_rid))

# 多数決のために送信元ノードごとのハッシュ値のヒストグラムを作成
# Majority Voting Logic
    print("\nMajority Voting")
    hash_hist = {}
    for senderid in rsp_for_rid:
        reqs = rsp_for_rid[senderid]
        for req in reqs:
#            print(req)
            hash = req['hash']
            if hash not in hash_hist:
                hash_hist[hash] = 1
            else:
                hash_hist[hash] += 1
#    print(hash_hist)

    max_count = 0
    total_count = 0
    selected_hash = b''
    for hash in hash_hist:
        count = hash_hist[hash] #hash値ごとの個数
        total_count += count

        if (max_count < count):
            max_count = count #最大頻度の個数
            selected_hash = hash #最大頻度のhash
#    req_for_rid['hash_hist'] = hash_hist
#    req_for_rid['selected_hash'] = selected_hash
#    req_for_rid['response_count'] = total_count
#    req_for_rid['max_count'] = max_count

    print("")
    approved_req = {}
    for sender in rsp_for_rid:
        rsp = rsp_for_rid[sender] #送信元ごとの新リング候補
#        print("request from node%s" % sender)
#        print(rsp)
#        print("")
        for rr in rsp:
#            print(rr)
            if  (selected_hash == rr['hash']): #ハッシュ値が一致する
                approved_req = rr
        print("Approved Req for %s  :%s" % (rID,approved_req)) #多数決結果
    requestList2 = {rID:approved_req}

print("Sorted Requests %s\n" % requestList2)

for approvedTransactions in requestList2:
    approvedRing = requestList2[approvedTransactions] #合意済み新リング候補
    print(approvedRing)


    newSegment = approvedRing['newTransaction']
    hash = approvedRing['hash']
    print("Approved new segment = %s  has = %s" % (newSegment,hash))
    #合意した　新リング候補を台帳に追加try
    print("Adding a new segment to the ledger")
    added = bledger.append_new_segment(newSegment,hash)
    if (added):
        print("Success")
    else:
        print("Failed to add the new segment")








print("\nLedjer = %s" % bledger.get_ledger())
print("Ledjer(obj) = %s" % bledger.get_ledger_objects())
print("last hash = %s " % bledger.get_last_hash())

print(bledger.get_acount_list())


print('\nGet Transactions')

length_of_ledger = bledger.get_ledger_length()
print("Ledger Length = %d" % length_of_ledger)

for i in range(0,length_of_ledger):
    ledger_segment = bledger.get_one_segment(i)
    print("ledger segment %d = %s" % (i,ledger_segment))

allChain = bledger.get_ledger_objects()
balance = {}
accountList = []
print(allChain)
for a_ring in allChain:
    print(a_ring)
    if 'transactions' in a_ring:
        transactions = a_ring['transactions']
        for transaction in transactions:
            balance[transaction['AccountID']] = transaction['balance']
            if transaction['AccountID'] not in accountList:
                accountList.append(transaction['AccountID'])
print(balance)
print(accountList)

ledger1 = bledger.get_ledger()
print(ledger1)

#clone
bank2 = bankLedger.bankLedger()
print(bank2.get_ledger())
bank2.make_it_clone(ledger1)

print(bank2.get_ledger())

allChain = bank2.get_ledger_objects()
balance = {}
accountList = []
print(allChain)
for a_ring in allChain:
    print(a_ring)
    if 'transactions' in a_ring:
        transactions = a_ring['transactions']
        for transaction in transactions:
            balance[transaction['AccountID']] = transaction['balance']
            if transaction['AccountID'] not in accountList:
                accountList.append(transaction['AccountID'])
print(balance)
print(accountList)
for account in accountList:
    balance = bledger.get_balance(account)
    print("account = %s  balance = %d" % (account,balance))
