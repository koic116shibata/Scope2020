import random
import d2ledger
import json
import binascii

nodeID = 'aaaaaaaa'
requestID_index = 10


ledgerID = d2ledger.generate_new_ID()
ledger = d2ledger.d2ledger(ledgerID)

print("Create a new ledger.   ID=%s" % ledger.getID())
print(ledger.get_ledger())
#print(ledger.get_ledger_objects())
#print("")
#print("last Hash %s" % ledger.get_last_hash())

#窓口ノードがスマホ等から新しいコマンドメッセージを受信
#receive a new request from end-terminal
newtransactionsRequestslist = []
newTransactionRequest = {'type':'initialBalance','AccountID':'A0000001','balance':1000}
newtransactionsRequestslist.append(newTransactionRequest)
newTransactionRequest = {'type':'pojntTransfer','from':'B0000002','to':'C0000003','amount':100}
newtransactionsRequestslist.append(newTransactionRequest)
print("\nNode <%s>  Received a new reuest from an end terminal:   %s" % (nodeID,newtransactionsRequestslist))

#ここでコマンドメッセージに含まれるアカウントIDを検証

#窓口ノードが他のノードにコマンドメッセージを中継送信
RequestID = ("%s%04d" % (nodeID,requestID_index))
requestID_index += 1
transfermessage = {'messageType':'commandRequest','originNode':nodeID,'RequestID':RequestID,'payload':newtransactionsRequestslist}
print('Transmit a new request to other nodes: %s\n' % transfermessage)

#他のノード群からコマンドメッセージを受信
#Receive new requests from nodes
receiveMessageList = [] #メッセージ受信バッファ
receiveMessageList.append(transfermessage) #loopback（自分で送ったメッセージを受信したとする）
print("Received new requests from other nodes%s\n" % receiveMessageList)

receivedCommandRequests = []
for newrequest in receiveMessageList:
    if (newrequest['messageType'] == 'commandRequest'): #受信バッファからコマンドメッセージを抽出
        requestID = newrequest['RequestID']
        if requestID not in receivedCommandRequests: #requestIDで重複排除(多数決しても良い)
            receivedCommandRequests.append({'RequestID':requestID,'payload':newrequest['payload']})
print("Received Command Requesrs from other nodes. %s" % receivedCommandRequests)

transmittedPackets = []

requestStatus = {}
for receivedMessage in receivedCommandRequests:
    receivedTransactionRequests = receivedMessage['payload']
    reveivedRequestID = receivedMessage['RequestID']
    requestStatus[reveivedRequestID] = {}

    #受信したコマンドメッセージの内容が正当(残高確認等)なコマンドであることを確認
#Check received Requests
    ledgerOperationRequests = []
    print("Checking Received Transaction Requests. ID:%s" % reveivedRequestID)
    for transaction in receivedTransactionRequests:
        print("   Checking %s" % transaction)
        if True:#OKの場合
            transactionType = transaction['type']
            if (transactionType == 'initialBalance'):
                if (True): #自分の台帳に該当アカウントが有る場合
                    newRing1 = {}
                    newRing1['type'] = 'balance'
                    newRing1['AccountID'] = transaction['AccountID']
                    newRing1['balance'] = transaction['balance']
                    ledgerOperationRequests.append(newRing1)
                    requestStatus[reveivedRequestID][newRing1['AccountID']] = {}
                    stat = {}
                    stat['status']  = 'processing'
                    stat['response'] = []
                    stat['startTime'] = 0
                    requestStatus[reveivedRequestID][newRing1['AccountID']] = stat
            if (transactionType == 'pojntTransfer'):
                if (True): #自分の台帳に該当アカウントが有る場合
                    newRing2 = {}
                    newRing2['type'] = 'balance'
                    newRing2['AccountID'] = transaction['to']
                    newRing2['balance'] = transaction['amount'] #取引後の金額
                    ledgerOperationRequests.append(newRing2)
                    stat = {}
                    stat['status']  = 'processing'
                    stat['response'] = []
                    stat['startTime'] = 0
                    requestStatus[reveivedRequestID][newRing2['AccountID']] = stat
                if (True):  # 自分の台帳に該当アカウントが有る場合
                    newRing3 = {}
                    newRing3['type'] = 'balance'
                    newRing3['AccountID'] = transaction['from']
                    newRing3['balance'] = - transaction['amount'] #取引後の金額
                    ledgerOperationRequests.append(newRing3)
                    stat = {}
                    stat['status']  = 'processing'
                    stat['response'] = []
                    stat['startTime'] = 0
                    requestStatus[reveivedRequestID][newRing3['AccountID']] = stat


    print("New Chain Candidate = %s" % ledgerOperationRequests)
#新しいチェインの候補を作成 hash計算含む
#Caliculate new Hash
    newhash = ledger.caliculate_hash(ledgerOperationRequests)
    print("hash = %s" % newhash)

# 新しいチェインの候補を送信
#Tranmit a candidate of a new segment

    transmitPacket = {}
    transmitPacket['messageType'] = 'newSegment'
    transmitPacket['RequestID'] = receivedMessage['RequestID']
    transmitPacket['sender'] = nodeID
    transmitPacket['newTransaction'] = ledgerOperationRequests
    transmitPacket['hash'] = newhash
    print("Transmit a candidate of new segment %s  to other nodes " % transmitPacket)
    transmittedPackets.append(transmitPacket) #送信パケット群

print("Processing Status Of Requests % s" % requestStatus)

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
    added = ledger.append_new_segment(newSegment,hash)
    if (added):
        print("Success")
    else:
        print("Failed to add the new segment")



print("\nLedjer = %s" % ledger.get_ledger())
print("Ledjer(obj) = %s" % ledger.get_ledger_objects())
print("last hash = %s " % ledger.get_last_hash())

print('\nGet Transactions')

length_of_ledger = ledger.get_ledger_length()
print("Ledger Length = %d" % length_of_ledger)

for i in range(0,length_of_ledger):
    ledger_segment = ledger.get_one_segment(i)
    print("ledger segment %d = %s" % (i,ledger_segment))

allChain = ledger.get_ledger_objects()
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