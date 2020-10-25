class node:
    def __init__(self,id,x,y):
        self.id = id
        self.x = x
        self.y = y
        self.recv_buf = []
        self.ledger = []
        self.send_buf = []
        self.sent_message = []
        self.receipt_message = []
        self.stat_receive_from = []
        self.stat_received = 0
        self.stat_just_received = False

        self.config_receive_range = 300 * 300

    def set_receive_range(self,range):
        self.config_receive_range = range * range

    def put_data(self,packet):
        sender = packet['sender']
        sender_x = packet['sender_x']
        sender_y = packet['sender_y']
        message_id = packet['payload']['MID']
#        if (self.id != sender):
        range = (self.x - sender_x) * (self.x - sender_x) + (self.y - sender_y) * (self.y - sender_y)
        if (range < self.config_receive_range                                                                                                                      ):
            if (message_id not in self.sent_message):
                self.stat_receive_from.append(sender)
                self.stat_received += 1
                if (message_id not in self.receipt_message):
                    self.recv_buf.append(packet)
                    self.receipt_message.append(message_id)
                    self.stat_just_received = True


    def clear_input_buf(self):
        self.stat_receive_from.clear()
        self.recv_buf.clear()
        self.stat_just_received = False

    def processing(self):
        self.send_buf.clear()
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
#                print("%s %d" % (sender,hopcount))
#                print(new_packet)
