from time import time


class Block:
    def __init__(self, index, previous_hash, transaction, proof, time=time()) :
        self.index=index
        self.previous_hash=previous_hash
        self.transactions=transaction
        self.proof=proof
        self.time = time 