from blockchain import Blockchain
import simpy

class NetworkNode:
    """Represents a single node in the P2P network"""
    def __init__(self, env, name, hash_rate):
        self.env = env
        self.name = name
        self.hash_rate = hash_rate
        self.blockchain = Blockchain(name)
        self.inbox = simpy.Store(self.env, capacity=float('inf'))
        self.env.process(self.run())

    def run(self):
        """SimPy process to handle incoming messages"""
        while True:
            message = yield self.inbox.get()
            if message[0] == 'transaction':
                self.blockchain.add_transaction(message[1])
            elif message[0] == 'chain':
                self.receive_chain(message[1])

    def receive_chain(self, chain):
        """Receive and validate a new chain"""
        self.blockchain.chain = chain
        self.blockchain.update_balances()
        return self.blockchain.is_chain_valid()

    def add_transaction(self, transaction):
        """Add transaction to node's blockchain"""
        return self.blockchain.add_transaction(transaction)

    def mine_block(self):
        """Mine a block on the node"""
        return self.blockchain.mine_block()