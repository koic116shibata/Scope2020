import d2dLedger
import random

class bankLedger:
    def __init__(self):
        id = generate_new_ID()
        self.myLedger = d2dLedger.d2dLedger(id)

    def make_it_clone(self,ledger):
        id = ledger[0]['LedgerID']
        self.myLedger = d2dLedger.d2dLedger(id)
        self.myLedger.set_ledger(ledger)

    def get_ledgerID(self):
        id = self.myLedger.get_ledger()[0]['LedgerID']
        return(id)

    def get_last_hash(self):
        return(self.myLedger.get_last_hash())

    def get_ledger(self):
        return(self.myLedger.get_ledger())

    def get_ledger_objects(self):
        ledger = self.myLedger.get_ledger()
        contents = []
        for segment in ledger:
            seg = {}
            for itemkey in segment:
                if ((itemkey == 'LedgerID') or (itemkey == 'hash')):
                    seg[itemkey] = segment[itemkey]
                else:
                    seg[itemkey] = d2dLedger.deserialize(segment[itemkey])
            contents.append(seg)
        return(contents)

    def caliculate_hash(self,transactions):
        return(self.myLedger.caliculate_hash(transactions))

    def append_new_segment(self,transactions,hash):
        return(self.myLedger.append_new_segment(transactions,hash))

    def get_ledger_length(self):
        return(self.myLedger.get_ledger_length())

    def get_one_segment(self,ix):
        return(self.myLedger.get_one_segment(ix))

    def get_account_list(self):
        ledgers = self.get_ledger_objects()
        balance = {}
        accountList = []
        for segment in ledgers:
            if 'transactions' in segment:
                transactions = segment['transactions']
                for transaction in transactions:
                    balance[transaction['AccountID']] = transaction['balance']
                    if transaction['AccountID'] not in accountList:
                        accountList.append(transaction['AccountID'])
        return(accountList)

    def get_balance(self,accountID):
        ledgers = self.get_ledger_objects()
        balance = 0
        for segment in ledgers:
            if 'transactions' in segment:
                transactions = segment['transactions']
                for transaction in transactions:
                    if (accountID == transaction['AccountID']):
                        balance = transaction['balance']
        return(balance)

    def get_candidate_of_new_block(self,receivedTransactionRequests):
        response = {}
        treadability = {}
        newsegments = []
        relatedAccounts = []
        presentAccounts = self.get_account_list()
        for transaction in receivedTransactionRequests:
            transactionType = transaction['type']
            relatedTransaction = False
            newSegment = {}
            newSegment['newTransaction'] = []
            if (transactionType == 'initialBalance'):
                accid = transaction['AccountID']
                treadability[accid] = 'unknown'
                if accid not in relatedAccounts:
                    relatedAccounts.append(accid)
                if accid in presentAccounts:  # 自分の台帳に該当アカウントが有る場合
                    newRing = {}
                    newRing['type'] = 'balance'
                    newRing['AccountID'] = accid
                    newRing['balance'] = transaction['balance']
                    treadability[accid] = 'valid'

                    newSegment = {}
                    hash = self.myLedger.caliculate_hash([newRing])
                    newSegment['newTransaction'] = [newRing]
                    newSegment['hash'] = hash
                    newsegments.append(newSegment)

                    relatedTransaction = True

            if (transactionType == 'pointTransfer'):
                accid = transaction['to']
                treadability[accid] = 'unknown'
                if accid not in relatedAccounts:
                    relatedAccounts.append(accid)
                if accid in presentAccounts:  # 自分の台帳に該当アカウントが有る場合
                    newRing = {}
                    newRing['type'] = 'balance'
                    newRing['AccountID'] = transaction['to']
                    balance1 = self.get_balance(transaction['to'])
                    newRing['balance'] = balance1 + transaction['amount']  # 取引後の金額
                    treadability[accid] = 'valid'
                    newSegment['newTransaction'].append(newRing)

                    relatedTransaction = True

                accid = transaction['from']
                treadability[accid] = 'unknown'
                if accid not in relatedAccounts:
                    relatedAccounts.append(accid)
                if accid in presentAccounts:  # 自分の台帳に該当アカウントが有る場合
                    newRing = {}
                    newRing['type'] = 'balance'
                    newRing['AccountID'] = transaction['from']
                    balance1 = self.get_balance(transaction['from'])
                    newRing['balance'] = balance1 - transaction['amount']  # 取引後の金額
                    if newRing['balance'] >= 0:
                        treadability[accid] = 'valid'
                        newSegment['newTransaction'].append(newRing)
                    else:
                        treadability[accid] = 'invalid'
                        newSegment['newTransaction'].append(newRing)

                    relatedTransaction = True

            if (transactionType == 'newAccount'):
                accid = transaction['AccountID']
                treadability[accid] = 'unknown'
                if accid not in presentAccounts:  # 自分の台帳に該当アカウントが<無い>場合
                    newRing = {}
                    newRing['type'] = 'balance'
                    newRing['AccountID'] = accid
                    newRing['balance'] = 0
                    treadability[accid] = 'valid'

                    newSegment = {}
                    hash = self.myLedger.caliculate_hash([newRing])
                    newSegment['newTransaction'] = [newRing]
                    newSegment['hash'] = hash

                    relatedTransaction = True

            if relatedTransaction:
                hash = self.myLedger.caliculate_hash(newSegment['newTransaction'])
                newSegment['hash'] = hash
                newsegments.append(newSegment)

        response['newsegments'] = newsegments
        response['relatedAccounts'] = relatedAccounts
        response['tradability'] = treadability
        return(response)




def generate_new_ID():
    tid = ''
    for i in range(0, 16):
        tid += "%02X" % random.randrange(0, 256)
    return(tid.encode())