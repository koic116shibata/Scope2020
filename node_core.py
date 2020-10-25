import bankLedger


class node_core:
    def __init__(self,nodeID):
        self.requestID_index = 0
        self.nodeID = nodeID
        self.request_status = {}

    def create_new_ledger(self):
        self.bledger = bankLedger.bankLedger()

    def get_request_status(self):
        return(self.request_status)

    def distribute_new_requests(self,received_packets):
        transmit_packets = []
        removing_packet  = []
        for packet in received_packets:
            if 'type' in packet:
                if packet['type'] == 'newRequest':
                    removing_packet.append(packet)
                    new_request = packet['payload']
                    RequestID = ("%s%04d" % (self.nodeID, self.requestID_index))
                    transfermessage = {'messageType': 'commandRequest', 'originNode': self.nodeID,
                                       'RequestID': RequestID,'payload': new_request}
                    self.requestID_index += 1
                    transmit_packets.append(transfermessage)
                    self.request_status[RequestID] = {}
                    self.request_status[RequestID]['status'] = 'generated'
                    self.request_status[RequestID]['erapsedTime'] = 0
        for packet in removing_packet:
            received_packets.remove(packet)
        return(transmit_packets)

    def generate_new_block(self,received_packets):
        transmit_packets = []
        removing_packet = []
        for packet in received_packets:
            if (packet['messageType'] == 'commandRequest'):  # 受信バッファからコマンドメッセージを抽出
                RequestID = packet['RequestID']
                removing_packet.append(packet)
                if RequestID not in self.request_status:  # requestIDで重複排除(多数決しても良い)
                    transmit_packets.append({'RequestID': RequestID, 'payload': packet['payload']})
                    self.request_status[RequestID] = {}
                    self.request_status[RequestID]['status'] = 'distributed'
                    self.request_status[RequestID]['erapsedTime'] = 0
                else:
                    if self.request_status[RequestID]['status'] == 'generated':
                        transmit_packets.append({'RequestID': RequestID, 'payload': packet['payload']})
                        self.request_status[RequestID]['status'] = 'distributed'

        distributePacket = []
        for receivedMessage in transmit_packets:
            payload = receivedMessage['payload']
            reveivedRequestID = receivedMessage['RequestID']

            self.request_status[reveivedRequestID] = {}
            accountlist = self.bledger.get_account_list()
            # 受信したコマンドメッセージの内容が正当(残高確認等)なコマンドであることを確認
            # Check received Requests
            #    ledgerOperationRequests = []
#            print("Core Node:RID %s Checking Received Transaction Requests." % (reveivedRequestID))

#            print("Core Node:RID %s   payload %s" % (reveivedRequestID,payload))

            response = self.bledger.get_candidate_of_new_block(payload)

            print("Core Node:RID %s  Response = %s" % (reveivedRequestID,response))
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

            self.request_status[reveivedRequestID]['status'] = 'processing'
            self.request_status[reveivedRequestID]['elapsedTime'] = 0
            self.request_status[reveivedRequestID]['response'] = {}
            for accid in relatedAccounts:
                self.request_status[reveivedRequestID]['response'][accid] = []

        for packet in removing_packet:
            received_packets.remove(packet)
        return(distributePacket)

    def store_new_block_candidates(self,received_packets):
        removing_packet = []
        accountlist = self.bledger.get_account_list()
        accountlist = ['A0000001', 'B0000002', 'C0000003'] #test
        for packet in received_packets:
            print("Storeing Packet %s" % packet)
            if (packet['messageType'] == 'newSegment'):
                removing_packet.append(packet)
                relatedAcounts = packet['relatedAccounts']
                related = False
                for acc in relatedAcounts:
                    if acc in accountlist:
                        related = True
                if related:
                    if (packet['messageType'] == 'newSegment'):
                        requestID = packet['RequestID']
    #                    print(requestID)
                        elapsedTime = self.request_status[requestID]['elapsedTime']
                        if elapsedTime < 10:
                            receivedNewSegment = {'sender': packet['sender'],
                                                  'tradabilty':packet['tradability'],
                                                  'newTransaction': packet['newTransaction'],
                                                  'hash': packet['hash']}
                            for transaction in packet['newTransaction']:
                                accid = transaction['AccountID']
                                appendFlag = True
                                for formerResponse in self.request_status[requestID]['response'][accid]:
                                    if packet['sender'] == formerResponse['sender']:
                                        appendFlag = False
                                if appendFlag:
                                    self.request_status[requestID]['response'][accid].append(receivedNewSegment)
                                    self.request_status[requestID]['status'] = 'receiving'
        for packet in removing_packet:
            received_packets.remove(packet)

        receivedNewSegments = {}
        approvedTransactionsList = {}
        for requestID in self.request_status:  # 他ノードを含む送信パケット群
#            print(requestID)
            status_for_rid = self.request_status[requestID]
#            print("status of RID%s\n%s" % (requestID, status_for_rid))
            receivedNewSegments[requestID] = []
            treadabilityList = {}
            if ((status_for_rid['status'] == 'receiving') and (status_for_rid['elapsedTime'] == 0)):
                responses = status_for_rid['response']
                for accid in responses:
                    treadabilityList[accid] = []
                    for response in responses[accid]:
                        print("response related Acc %s \n%s" % (accid, response))
                        receivedNewSegment = {'sender': response['sender'],
                                              'newTransaction': response['newTransaction'], 'hash': response['hash'],
                                              'AccountID': accid}
                        receivedNewSegments[requestID].append(receivedNewSegment)
                        treadabilityList[accid].append(response['tradabilty'])

                responses = receivedNewSegments[requestID]
                print("Tradability %s" % (treadabilityList))

                votinglist = {}
                for acc2 in treadabilityList:
                    states = treadabilityList[acc2]
                    print(acc2)
                    print(states)
                    for state in states:
                        for acc3 in state:
                            print(acc3)
                            st = state[acc3]
                            if acc3 not in votinglist:
                                votinglist[acc3] = {'valid':0,'unknown':0,'invalid':0}
                            if st not in votinglist[acc3]:
                                votinglist[acc3][st] = 0
                            votinglist[acc3][st] += 1
                print("voting list %s" % votinglist)
                votingStat = {}
                votingResult = False
                if (len(votinglist) > 0):
                    votingResult = True
                for acc in votinglist:
                    stat = votinglist[acc]
                    print(stat)
                    votingStat[acc] = 'NG'
                    if (stat['valid'] > stat['invalid']) and (stat['valid'] >= 1):
                        votingStat[acc] = 'OK'
                    else:
                        votingResult = False
                print(votingStat)
                print(votingResult)

                    # Majority Voting Logic
                if votingResult:
        #            print("\nMajority Voting for %s" % requestID)
        # 多数決のために送信元ノードごとのハッシュ値のヒストグラムを作成
                    hash_hist = {}
    #                print(responses)
                    transaction_table = {}
                    for response in responses:
                        sender = response['sender']
                        transactions = response['newTransaction']
                        account = response['AccountID']
                        hash = response['hash']
                        transaction_table[hash] = transactions
                        if account not in hash_hist:
                            hash_hist[account] = {}
        #                print(hash_hist)
                        if hash not in hash_hist[account]:
                            hash_hist[account][hash] = 1
                        else:
                            hash_hist[account][hash] += 1
        #            print(hash_hist)

                    selected_hash = {}
                    selected_transactions = {}
                    for acc in hash_hist:
                        max_count = 0
                        total_count = 0
                        selected_hash[acc] = {}
                        selected_transactions[acc] = {}
                        for hash in hash_hist[acc]:
        #                    print(hash)
                            count = hash_hist[acc][hash]  # hash値ごとの個数
                            total_count += count

                            if (max_count < count):
                                max_count = count  # 最大頻度の個数
                                selected_hash[acc] = hash  # 最大頻度のhash
                                selected_transactions[acc] = transaction_table[hash]
        #            print(selected_hash)
        #            print(selected_transactions)

                    print("")
                    selected_segment = {}
                    for acc in selected_hash:
                        selected_segment[acc] = {'newTransaction': selected_transactions[acc], 'hash': selected_hash[acc]}
                    approvedTransactionsList[requestID] = selected_segment
                    self.request_status[requestID]['status'] = 'Closed'
                    self.request_status[requestID]['response'] = {}
                else:
                    self.request_status[requestID]['status'] = 'Failed'
                    self.request_status[requestID]['response'] = {}
                    self.request_status[requestID]['reason'] = 'Voting'
                    self.request_status[requestID]['voting'] = votingStat

#        print("Approved Segments %s\n" % approvedTransactionsList)

        for rid in approvedTransactionsList:
            approvedSegment = approvedTransactionsList[rid]  # 合意済み新リング候補
#            print(approvedSegment)
            related = False
            acclist = []
            for acc in approvedSegment:
                if acc in accountlist:
                    related = True
                    acclist.append(acc)
            acc = acclist[0]

            if related:
                newSegment = approvedSegment[acc]['newTransaction']
                hash = approvedSegment[acc]['hash']
                print("Approved new segment = %s  hash = %s" % (newSegment, hash))
#                print(self.bledger.caliculate_hash(newSegment))
                # 合意した　新リング候補を台帳に追加try
#                print("Adding a new segment to the ledger")

                added = self.bledger.append_new_segment(newSegment, hash)
                if (added):
#                    print("Success")
                    self.request_status[rid]['status'] = 'Success'
                    self.request_status[rid]['response'] = {}
                else:
#        print("Failed to add the new segment")
                    self.request_status[rid]['status'] = 'Failed'
                    self.request_status[rid]['response'] = {}
                    self.request_status[rid]['reason'] = 'hash not match'

    def get_account_list(self):
        return(self.bledger.get_account_list())

    def get_balance(self,accountID):
        return(self.bledger.get_balance(accountID))

    def set_initial_account(self,accountID,balance): #DEBUG only
        newRing = {}
        newRing['type'] = 'balance'
        newRing['AccountID'] = accountID
        newRing['balance'] = balance

        hash = self.bledger.caliculate_hash([newRing])
        self.bledger.append_new_segment([newRing],hash)
