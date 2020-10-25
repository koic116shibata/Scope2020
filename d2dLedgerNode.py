import node_core_M

class node:
    def __init__(self,id,x,y):
        self.id = id
        self.x = x
        self.y = y
        self.m_count = 1
        self.recv_buf = []
        self.send_buf = []
        self.sent_message = []
        self.receipt_message = []
        self.stat_receive_from = []
        self.stat_received = 0
        self.stat_just_received = False
        self.ledgerNames = ''

        self.config_receive_range = 300 * 300

        self.node_core = node_core_M.node_core(id)

    def set_receive_range(self,range):
        self.config_receive_range = range * range

    def create_new_ledger(self):
        self.node_core.create_new_ledger()

    def create_clone_ledger(self,ledgerContents):
        self.node_core.create_clone_ledger(ledgerContents)

    def set_initial_account(self,num,accountID,amount):
        self.node_core.set_initial_account(num,accountID,amount)

    def set_node_wait_time(self,waitTime):
        self.node_core.set_wait_time(waitTime)

    def get_ledger_ID_list(self):
        return(self.node_core.get_ledger_ID_list())

    def get_ledger_contents(self,ledgerID):
        return(self.node_core.get_ledger_contents(ledgerID))

    def receive_new_request(self,packets):
        self.send_buf.clear()
        distribute_packets = self.node_core.distribute_new_requests(packets)
        rids = []
        for content in distribute_packets:
            s_packet = {}
            s_packet['sender'] = self.id
            s_packet['sender_x'] = self.x
            s_packet['sender_y'] = self.y
            s_packet['hopcount'] = 0
            payload = {}
            payload['MID'] = self.id + ("%05d" % self.m_count)
            self.m_count += 1
            payload['contents'] = content
            s_packet['payload'] = payload
            self.send_buf.append(s_packet)
            rid = payload['contents']['RequestID']
            rids.append(rid)
        return(rids)
#            self.sent_message.append(payload['MID'])



    def put_data(self,packets):
        self.recv_buf = []
        for packet in packets:
            sender = packet['sender']
            sender_x = packet['sender_x']
            sender_y = packet['sender_y']
            message_id = packet['payload']['MID']
    #        self.send_buf.clear()
    #        if (self.id != sender):
            range = (self.x - sender_x) * (self.x - sender_x) + (self.y - sender_y) * (self.y - sender_y)
            if (range < self.config_receive_range):
                if (message_id not in self.sent_message):
                    self.stat_receive_from.append(sender)
                    self.stat_received += 1
    #                print(message_id)
    #                print(self.receipt_message)
                    if (message_id not in self.receipt_message):
                        self.recv_buf.append(packet)
                        self.receipt_message.append(message_id)
                        self.stat_just_received = True
        commandRequests = []
        receivedNewSegments = []
        for packet in self.recv_buf:
            contents = packet['payload']['contents']
#            print("node %s Recieved Packet %s " % (self.id,contents))
            if contents['messageType'] == 'commandRequest':
                commandRequests.append(contents)
            if contents['messageType'] == 'newSegment':
                receivedNewSegments.append(contents)
        if len(commandRequests) > 0:
#            print("new commands = %s" % commandRequests)
            distribute_packets = self.node_core.generate_new_block(commandRequests)
            if len(distribute_packets) > 0:
#                print("node %s Distribute new blocks to other nodes:%s" % (self.id,distribute_packets))
                for content in distribute_packets:
                    s_packet = {}
                    s_packet['sender'] = self.id
                    s_packet['sender_x'] = self.x
                    s_packet['sender_y'] = self.y
                    s_packet['hopcount'] = 0
                    payload = {}
                    payload['MID'] = self.id + ("%05d" % self.m_count)
                    self.m_count += 1
                    payload['contents'] = content
                    s_packet['payload'] = payload
                    self.send_buf.append(s_packet)
                    self.sent_message.append(payload['MID'])

#        if len(receivedNewSegments) > 0:
#            print("new segments = %s" % receivedNewSegments)
        self.node_core.store_new_block_candidates(receivedNewSegments)

        for recv_packet in self.recv_buf:
            sender = recv_packet['sender']
            hopcount = recv_packet['hopcount']
            payload = recv_packet['payload']
            message_id = payload['MID']


            duplication = False
            for trans_packet in self.send_buf:
                t_mid = trans_packet['payload']['MID']
                if (message_id == t_mid):
                    duplication = True
            if (not duplication):
                new_packet = {}
                new_packet['sender'] = self.id
                new_packet['sender_x'] = self.x
                new_packet['sender_y'] = self.y
                new_packet['hopcount'] = hopcount  + 1
                new_packet['payload'] = payload
                self.send_buf.append(new_packet)
                self.sent_message.append(message_id)
        self.recv_buf.clear()

    def clear_input_buf(self):
        self.stat_receive_from.clear()
        self.recv_buf.clear()
        self.stat_just_received = False

    def get_status(self, requestID):
        status = self.node_core.get_request_status()
        #        print(status)
        r_status = {}
        if requestID in status:
            if 'status' in status[requestID]:
                r_status = status[requestID]
        return (r_status)

    def get_status_digest(self,requestID):
        status = self.node_core.get_request_status()
#        print(status)
        state = 'idle'
        if requestID in status:
            if 'status' in status[requestID]:
                state = status[requestID]['status']
        return(state)

    def get_status_response_stat(self,requestID):
        status = self.node_core.get_request_status()
        voting = {}
        if requestID in status:
            if 'voting' in status[requestID]:
                voting = status[requestID]['voting']
        return(voting)

    def get_status_response_count(self,requestID):
        status = self.node_core.get_request_status()
        stats = []
        if requestID in status:
            if 'repliedNodes' in status[requestID]:
                for accid in status[requestID]['repliedNodes']:
                    stats.append(len(status[requestID]['repliedNodes'][accid]))
        return(stats)

    def proceed_time(self):
        self.node_core.proceed_time()

    def add_ledger_name(self,name):
        self.ledgerNames += (" " + name)

    def get_ledger_name(self):
        return(self.ledgerNames)

    def get_account_list(self):
        return(self.node_core.get_account_list())

    def get_balance(self,accountID):
        return(self.node_core.get_balance(accountID))
