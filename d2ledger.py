import random
import json
import binascii
import hashlib

class d2ledger:
    def __init__(self,id):
        self.ledger = []
        self.id = id
        hash = hashlib.sha256(self.id).hexdigest().encode()
        self.index = 0
        self.ledger.append({'LedgerID':self.id,'hash':hash})


    def getID(self):
        return(self.id)

    def get_last_hash(self):
        lastcontents = self.ledger[-1]
        last_hash = lastcontents['hash']
        return(last_hash)

    def get_ledger(self):
        return(self.ledger)

    def get_ledger_objects(self):
        ledger = self.ledger
        contents = []
        for segment in ledger:
            seg = {}
            for itemkey in segment:
                if ((itemkey == 'LedgerID') or (itemkey == 'hash')):
                    seg[itemkey] = segment[itemkey]
                else:
                    seg[itemkey] = deserialize(segment[itemkey])
            contents.append(seg)
        return(contents)


    def caliculate_hash(self,transactions):
        lasthash = self.get_last_hash()
        serialized_transactions = serialize(transactions)
        newhash = hashlib.sha256(lasthash+serialized_transactions).hexdigest().encode()
        validated = True
        return(newhash)

    def append_new_segment(self,transactions,hash):
        lasthash = self.get_last_hash()
        serialized_transactions = serialize(transactions)
        newhash = hashlib.sha256(lasthash+serialized_transactions).hexdigest().encode()
        inspection = False
        if (hash == newhash):
            self.index += 1
            content = {'transactions':serialized_transactions,'hash':newhash}
            self.ledger.append(content)
            inspection = True
        return(inspection)

    def get_ledger_length(self):
        return(self.index + 1)

    def get_one_segment(self,ix):
        segment = self.ledger[ix]
        return(segment)


def serialize(obj):
    jsonencoded_obj = json.dumps(obj).encode('utf-8')
    serialized_obj = binascii.hexlify(jsonencoded_obj)
    return(serialized_obj)

def deserialize(binaryData):
    objstr = binascii.unhexlify(binaryData).decode('utf-8')
    obj = json.loads(objstr)
    return(obj)

def generate_new_ID():
    tid = ''
    for i in range(0, 16):
        tid += "%02X" % random.randrange(0, 256)
    return(tid.encode())