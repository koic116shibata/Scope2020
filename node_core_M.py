import bankLedger
import json
import binascii
import hashlib

class node_core:
    def __init__(self,nodeID):
        self.requestID_index = 0
        self.nodeID = nodeID
        self.request_status = {}
        self.ledgers = []
        self.wait_time = 5

    def create_new_ledger(self):
        new_ledger = bankLedger.bankLedger()
        self.ledgers.append(new_ledger)

    def create_clone_ledger(self,ledgerContent):
        new_ledger = bankLedger.bankLedger()
        newLedgerContent = []
        for content in ledgerContent:
            newLedgerContent.append(content)
        new_ledger.make_it_clone(newLedgerContent)
        self.ledgers.append(new_ledger)
        return()

    def get_request_status(self):
        return(self.request_status)

    def set_wait_time(self,waitTime):
        self.wait_time = waitTime

    def distribute_new_requests(self,received_packets):
        transmit_packets = []
        for packet in received_packets:
            if 'type' in packet:
                if packet['type'] == 'newRequest':
                    new_request = packet['payload']
                    RequestID = ("%s_%04d" % (self.nodeID, self.requestID_index))
                    transfermessage = {'messageType': 'commandRequest', 'originNode': self.nodeID,
                                       'RequestID': RequestID,'payload': new_request}
                    self.requestID_index += 1
                    transmit_packets.append(transfermessage)
                    self.request_status[RequestID] = {}
                    self.request_status[RequestID]['status'] = 'generated'
                    self.request_status[RequestID]['erapsedTime'] = 0
        return(transmit_packets)

    def generate_new_block(self,received_packets):
        transmit_packets = []
        distributePacket = []
        for bledger in self.ledgers:
            for packet in received_packets:
                if (packet['messageType'] == 'commandRequest'):  # 受信バッファからコマンドメッセージを抽出
                    RequestID = packet['RequestID']
                    if RequestID not in self.request_status:  # requestIDで重複排除(多数決しても良い)
                        transmit_packets.append({'RequestID': RequestID, 'payload': packet['payload']})
                        self.request_status[RequestID] = {}
                        self.request_status[RequestID]['status'] = 'distributed'
                        self.request_status[RequestID]['erapsedTime'] = 0
                    else:
                        if self.request_status[RequestID]['status'] == 'generated':
                            transmit_packets.append({'RequestID': RequestID, 'payload': packet['payload']})
                            self.request_status[RequestID]['status'] = 'distributed'

            for receivedMessage in transmit_packets:
                payload = receivedMessage['payload']
                reveivedRequestID = receivedMessage['RequestID']

                self.request_status[reveivedRequestID] = {}
                accountlist = bledger.get_account_list()
                # 受信したコマンドメッセージの内容が正当(残高確認等)なコマンドであることを確認
                # Check received Requests
                #    ledgerOperationRequests = []
    #            print("Core Node:RID %s Checking Received Transaction Requests." % (reveivedRequestID))

    #            print("Core Node:RID %s   payload %s" % (reveivedRequestID,payload))

                response = bledger.get_candidate_of_new_block(payload)

#                print("Core Node:RID %s  Response = %s" % (reveivedRequestID,response))
                tradability = response['tradability']
                relatedAccounts = response['relatedAccounts']
    #            print(relatedAccounts)
    #            print(accountlist)
                related = False
                for acc in relatedAccounts:
                    if acc in accountlist:
                        related = True
                if related:
                    for newSegment in response['newsegments']:
                        newTransaction = newSegment['newTransaction']
                        newhash = newSegment['hash']
        #                print("\nCore Node:RID %s New Chain Candidate = %s" % (reveivedRequestID,newTransaction))
        #                print("Core Node:RID %s hash = %s" % (reveivedRequestID,newhash))

                        # 新しいチェインの候補を送信
                        # Tranmit a candidate of a new segment

                        transmitPacket = {}
                        transmitPacket['messageType'] = 'newSegment'
                        transmitPacket['RequestID'] = reveivedRequestID
                        transmitPacket['sender'] = self.nodeID
                        transmitPacket['tradability'] = tradability
                        transmitPacket['relatedAccounts'] = relatedAccounts
                        tradable = True
    #                    for id in tradability:
    #                        if tradability[id] == 'invalid':
    #                            tradable = False
                        if tradable:
                            transmitPacket['newTransaction'] = newTransaction
                            transmitPacket['hash'] = newhash
                        #    print("Transmit a candidate of new segment %s  to other nodes " % transmitPacket)
                        distributePacket.append(transmitPacket)  # 送信パケット群

                self.request_status[reveivedRequestID]['status'] = 'waiting'
                self.request_status[reveivedRequestID]['elapsedTime'] = 0
                self.request_status[reveivedRequestID]['response'] = {}
                self.request_status[reveivedRequestID]['repliedNodes'] = {}
#                for accid in relatedAccounts:
#                    self.request_status[reveivedRequestID]['response'][accid] = []

        return(distributePacket)

    def store_new_block_candidates(self,received_packets):
        accountlist = self.get_account_list()
        for packet in received_packets:
#            print("Receive new segment Packet %s" % packet)
            if (packet['messageType'] == 'newSegment'):
                relatedAcounts = packet['relatedAccounts']
                related = False
                for acc in relatedAcounts:
                    if acc in accountlist:
                        related = True
                if related:
                    if (packet['messageType'] == 'newSegment'):
                        requestID = packet['RequestID']
    #                    print(requestID)
                        if requestID not in self.request_status:
                            self.request_status[requestID] = {}
                            self.request_status[requestID]['elapsedTime'] = 0
                            self.request_status[requestID]['response'] = {}
                            self.request_status[requestID]['status']= 'receiving'
                            self.request_status[requestID]['repliedNodes'] = {}
                        if (self.request_status[requestID]['status'] == 'receiving') or (self.request_status[requestID]['status'] == 'waiting'):
                            elapsedTime = self.request_status[requestID]['elapsedTime']
                            if elapsedTime <= self.wait_time:
                                receivedNewSegment = {'sender': packet['sender'],
                                                      'tradabilty':packet['tradability'],
                                                      'newTransaction': packet['newTransaction'],
                                                      'hash': packet['hash']}
                                for transaction in packet['newTransaction']:
                                    accid = transaction['AccountID']
                                    appendFlag = True
                                    if accid in self.request_status[requestID]['response']:
                                        if packet['sender'] not in self.request_status[requestID]['repliedNodes'][accid]:
                                            self.request_status[requestID]['response'][accid].append(receivedNewSegment)
                                            self.request_status[requestID]['repliedNodes'][accid].append(packet['sender'])
                                            self.request_status[requestID]['status'] = 'receiving'
                                    else:
                                        self.request_status[requestID]['response'][accid] = []
                                        self.request_status[requestID]['response'][accid].append(receivedNewSegment)
                                        self.request_status[requestID]['repliedNodes'][accid] = []
                                        self.request_status[requestID]['repliedNodes'][accid].append(packet['sender'])
                                        self.request_status[requestID]['status'] = 'receiving'

        receivedNewSegments = {}
        approvedTransactionsList = {}
        for requestID in self.request_status:  # 他ノードを含む送信パケット群
            status_for_rid = self.request_status[requestID]
#            print("status of RID%s\n%s" % (requestID, status_for_rid))
            receivedNewSegments[requestID] = []
            treadabilityList = {}
            votinglist = {}
            if ((status_for_rid['status'] == 'receiving') and (status_for_rid['elapsedTime'] >= self.wait_time)):
                responses = status_for_rid['response']
                for accid in responses:
                    treadabilityList[accid] = []
                    for response in responses[accid]:
#                            print("response related Acc %s \n%s" % (accid, response))
                        receivedNewSegment = {'sender': response['sender'],
                                              'newTransaction': response['newTransaction'], 'hash': response['hash'],
                                              'AccountID': accid}
                        receivedNewSegments[requestID].append(receivedNewSegment)
                        treadabilityList[accid].append(response['tradabilty'])

                responses = receivedNewSegments[requestID]
#                    print("Tradability %s" % (treadabilityList))

                for acc2 in treadabilityList:
                    states = treadabilityList[acc2]
#                        print(acc2)
#                        print(states)
                    for state in states:
                        for acc3 in state:
#                                print(acc3)
                            st = state[acc3]
                            if acc3 not in votinglist:
                                votinglist[acc3] = {'valid':0,'unknown':0,'invalid':0}
                            if st not in votinglist[acc3]:
                                votinglist[acc3][st] = 0
                            votinglist[acc3][st] += 1
#                    print("voting list %s" % votinglist)
                votingStat = {}
                votingResult = False
                if (len(votinglist) > 0):
                    votingResult = True
                for acc in votinglist:
                    stat = votinglist[acc]
#                        print(stat)
                    votingStat[acc] = 'NG'
                    if (stat['valid'] > stat['invalid']) and (stat['valid'] >= 1):
                        votingStat[acc] = 'OK'
                    else:
                        votingResult = False
#                    print(votingStat)
#                    print(votingResult)

                    # Majority Voting Logic
                hash_hist = {}
                if votingResult:
        #            print("\nMajority Voting for %s" % requestID)
        # 多数決のために送信元ノードごとのハッシュ値のヒストグラムを作成
                    transaction_table = {}
                    hash_table = {}
                    for response in responses:
                        account = response['AccountID']
                        hash2 = caliculate_tran_hash(response['newTransaction'],response['hash'])
                        transaction_table[hash2] = response['newTransaction']
                        hash_table[hash2] = response['hash']
                        if account not in hash_hist:
                            hash_hist[account] = {}
                        if hash2 not in hash_hist[account]:
                            hash_hist[account][hash2] = 1
                        else:
                            hash_hist[account][hash2] += 1


                    selected_hash = {}
                    selected_transactions = {}
                    for acc in hash_hist:
                        max_count = 0
                        total_count = 0
                        selected_hash[acc] = {}
                        selected_transactions[acc] = {}
                        for hash2 in hash_hist[acc]:
        #                    print(hash)
                            count = hash_hist[acc][hash2]  # hash値ごとの個数
                            total_count += count

                            if (max_count < count):
                                max_count = count  # 最大頻度の個数
                                selected_hash[acc] = hash_table[hash2]  # 最大頻度のhash
                                selected_transactions[acc] = transaction_table[hash2]
#                    print(selected_hash)
        #            print(selected_transactions)

#                        print("")
                    selected_segment = {}
                    for acc in selected_hash:
                        selected_segment[acc] = {'newTransaction': selected_transactions[acc], 'hash': selected_hash[acc]}
                    approvedTransactionsList[requestID] = selected_segment
                    self.request_status[requestID]['status'] = 'Closed'
                    self.request_status[requestID]['response'] = {}
                else:
                    self.request_status[requestID]['status'] = 'NotApproved'
                    self.request_status[requestID]['response'] = {}
                    self.request_status[requestID]['reason'] = 'Voting'
#                    self.request_status[requestID]['voting'] = votinglist
                self.request_status[requestID]['voting'] = votinglist
                self.request_status[requestID]['hashList'] = ("%s" % hash_hist)

#        print(self.ledgers)
        for rid in approvedTransactionsList:
            success = True
            for bledger in self.ledgers:

                accountlist = bledger.get_account_list()
#                print("")
#                print(rid)
#                print(self.request_status[rid]['status'])
                if ((self.request_status[rid]['elapsedTime'] >= self.wait_time) and
                        ((self.request_status[rid]['status'] == 'receiving') or
                         (self.request_status[rid]['status'] >= 'Closed'))):
                    approvedSegment = approvedTransactionsList[rid]  # 合意済み新リング候補
#                    print("Approved Segments %s" % approvedSegment)
                    related = False
                    completed_acclist = []
                    for acc in approvedSegment:
                        if acc in accountlist:
                            if acc not in completed_acclist:
                                newSegment = approvedSegment[acc]['newTransaction']
                                hash = approvedSegment[acc]['hash']
#                                print("Approved new segment = %s  hash = %s" % (newSegment, hash))

                                added = bledger.append_new_segment(newSegment, hash)
                                if not added:
                                    success = False
                                for transaction in newSegment:
                                    if 'AccountID' in transaction:
                                        c_acc = transaction['AccountID']
                                        completed_acclist.append(c_acc)

            if (success):
    #                                print("Success")
                self.request_status[rid]['status'] = 'Success'
                self.request_status[rid]['response'] = {}
            else:
    #                                print("Failed to add the new segment")
                self.request_status[rid]['status'] = 'Failed'
                self.request_status[rid]['response'] = {}
                self.request_status[rid]['reason'] = ('hash not match')

    def proceed_time(self):
        for rid in self.request_status:
            if (self.request_status[rid]['status'] == 'receiving') or (self.request_status[rid]['status'] == 'processing'):
                self.request_status[rid]['elapsedTime'] += 1


    def get_account_list(self):
        accountlist = []
        for bledger in self.ledgers:
            accl = bledger.get_account_list()
            for acc in accl:
                accountlist.append(acc)
        return(accountlist)

    def get_balance(self,accountID):
        balance = 0
        for bledger in self.ledgers:
            accl = bledger.get_account_list()
            if accountID in accl:
                balance = bledger.get_balance(accountID)
        return(balance)

    def get_ledger_ID_list(self):
        ID_list = []
        for ledger in self.ledgers:
            ID_list.append(ledger.get_ledgerID())
        return(ID_list)

    def get_ledger_contents(self,ledgerID):
        ledgerContents = []
        for ledger in self.ledgers:
            if ledgerID == ledger.get_ledgerID():
                ledgerContents = ledger.get_ledger()
        return(ledgerContents)


    def set_initial_account(self,ledgerNo,accountID,balance): #DEBUG only
        bledger = self.ledgers[ledgerNo]
        newRing = {}
        newRing['type'] = 'balance'
        newRing['AccountID'] = accountID
        newRing['balance'] = balance

        hash = bledger.caliculate_hash([newRing])
        bledger.append_new_segment([newRing],hash)

def caliculate_tran_hash(transaction,hash):
    jsonencoded_obj = json.dumps(transaction).encode('utf-8')
    o_hash = hashlib.sha256(jsonencoded_obj+hash).hexdigest().encode()
    return (o_hash)