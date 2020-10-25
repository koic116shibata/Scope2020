import json
import binascii
import hashlib

class d2dLedger:
    def __init__(self,id):
        self.ledger = []
        self.id = id
        hash = hashlib.sha256(self.id).hexdigest().encode()
        self.ledger.append({'LedgerID':self.id,'hash':hash})

#    def getID(self):
#        return(self.id)

    def get_last_hash(self):
        lastcontents = self.ledger[-1]
        last_hash = lastcontents['hash']
        return(last_hash)

    def get_ledger(self):
        return(self.ledger)

    def set_ledger(self,ledger):
        self.id = ledger[0]['LedgerID']
        self.ledger = ledger

    def caliculate_hash(self,transactions):
        lasthash = self.get_last_hash()
        serialized_transactions = serialize(transactions)
        newhash = hashlib.sha256(lasthash+serialized_transactions).hexdigest().encode()
        return(newhash)

    def append_new_segment(self,transactions,hash):
        lasthash = self.get_last_hash()
        serialized_transactions = serialize(transactions)
        newhash = hashlib.sha256(lasthash+serialized_transactions).hexdigest().encode()
#        print("hash compareing. for %s  caliculated:%s  presented*%s" % (transactions,newhash,hash))
        inspection = False
        if (hash == newhash):
            content = {'transactions':serialized_transactions,'hash':newhash}
            self.ledger.append(content)
            inspection = True
        return(inspection)

    def get_ledger_length(self):
        return(len(self.ledger))

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

