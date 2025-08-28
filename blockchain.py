import hashlib
import json
import time
import random
from datetime import datetime
import uuid
import simpy

class Transaction:
    """Represents a blockchain transaction"""
    def __init__(self, sender, recipient, amount, transaction_id=None):
        self.transaction_id = transaction_id or str(uuid.uuid4())[:8]
        self.sender = sender
        self.recipient = recipient
        self.amount = float(amount)
        self.timestamp = time.time()

    def to_dict(self):
        return {
            'transaction_id': self.transaction_id,
            'sender': self.sender,
            'recipient': self.recipient,
            'amount': self.amount,
            'timestamp': self.timestamp,
            'date': datetime.fromtimestamp(self.timestamp).strftime('%Y-%m-%d %H:%M:%S')
        }

    def calculate_hash(self):
        """Calculate transaction hash"""
        tx_data = json.dumps({
            'sender': self.sender,
            'recipient': self.recipient,
            'amount': self.amount,
            'timestamp': self.timestamp
        }, sort_keys=True)
        return hashlib.sha256(tx_data.encode()).hexdigest()

class Block:
    """Represents a blockchain block"""
    def __init__(self, index, transactions, timestamp, previous_hash, nonce=0):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_data = json.dumps({
            'index': self.index,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'timestamp': self.timestamp,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce
        }, sort_keys=True)
        return hashlib.sha256(block_data.encode()).hexdigest()

    def mine_block(self, difficulty, hash_rate=1.0):
        """Mine block using Proof of Work"""
        target = "0" * difficulty
        start_time = time.time()
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
            if hash_rate < 1.0:
                time.sleep(0.001 / max(hash_rate, 0.1))
        return time.time() - start_time

    def to_dict(self):
        return {
            'index': self.index,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'timestamp': self.timestamp,
            'date': datetime.fromtimestamp(self.timestamp).strftime('%Y-%m-%d %H:%M:%S'),
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'hash': self.hash
        }

class Blockchain:
    """Main blockchain implementation"""
    def __init__(self, node_name="Main"):
        self.node_name = node_name
        self.chain = [self.create_genesis_block()]
        self.difficulty = 3
        self.pending_transactions = []
        # Only 3 nodes with starting balances
        self.balances = {'Node1': 100, 'Node2': 100, 'Node3': 100}
        self.is_mining = False

    def create_genesis_block(self):
        """Genesis block (empty, no auto transactions)"""
        return Block(0, [], time.time(), "0")

    def get_latest_block(self):
        return self.chain[-1]

    def add_transaction(self, transaction):
        if self.validate_transaction(transaction):
            self.pending_transactions.append(transaction)
            return True
        return False

    def validate_transaction(self, transaction):
        if transaction.sender not in self.balances:
            self.balances[transaction.sender] = 0
        return self.balances[transaction.sender] >= transaction.amount

    def mine_block(self):
        if self.is_mining or not self.pending_transactions:
            return None
        self.is_mining = True
        try:
            transactions = self.pending_transactions.copy()
            block = Block(len(self.chain), transactions, time.time(), self.get_latest_block().hash)
            mining_time = block.mine_block(self.difficulty)
            self.chain.append(block)
            self.pending_transactions = []
            self.update_balances()
            return {
                'block': block,
                'mining_time': round(mining_time, 2),
                'transactions_count': len(transactions)
            }
        finally:
            self.is_mining = False

    def update_balances(self):
        """Reset balances and recalc from chain"""
        self.balances = {'Node1': 100, 'Node2': 100, 'Node3': 100}
        for block in self.chain:
            for tx in block.transactions:
                if tx.sender != "system":
                    self.balances[tx.sender] = self.balances.get(tx.sender, 0) - tx.amount
                self.balances[tx.recipient] = self.balances.get(tx.recipient, 0) + tx.amount

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i-1]
            if current.hash != current.calculate_hash() or current.previous_hash != previous.hash:
                return False
        return True

    def to_dict(self):
        return {
            'node_name': self.node_name,
            'chain': [block.to_dict() for block in self.chain],
            'pending_transactions': [tx.to_dict() for tx in self.pending_transactions],
            'balances': self.balances,
            'chain_info': {
                'chain_length': len(self.chain),
                'pending_transactions': len(self.pending_transactions),
                'is_mining': self.is_mining,
                'is_valid': self.is_chain_valid()
            }
        }

class NetworkSimulator:
    """Simulates a P2P network and double-spending attacks using SimPy"""
    def __init__(self):
        self.env = simpy.Environment()
        self.main_chain = Blockchain("Main")
        self.attacker_chain = None
        self.attack_in_progress = False
        self.event_records = []
        # Only 3 nodes
        self.nodes = [
            {'name': 'Node1', 'hash_rate': 0.40},
            {'name': 'Node2', 'hash_rate': 0.35},
            {'name': 'Node3', 'hash_rate': 0.25}
        ]
        self.network = simpy.Store(self.env, capacity=float('inf'))

    def broadcast_transaction(self, transaction):
        self.env.process(self._broadcast_transaction(transaction))
        return self.main_chain.add_transaction(transaction)

    def _broadcast_transaction(self, transaction):
        yield self.env.timeout(0.1)
        self.network.put(('transaction', transaction))

    def propagate_chain(self):
        yield self.env.timeout(0.1)
        self.record_event("Chain propagated to all nodes")

    def execute_attack(self, attacker, victim, amount, network_delay, hash_rate):
        """Any node can be attacker"""
        if self.attack_in_progress:
            return {"success": False, "error": "Attack already in progress"}
        self.attack_in_progress = True
        self.event_records = []
        try:
            self.record_event(f"Attack started by {attacker}")
            legitimate_tx = Transaction(attacker, victim, amount)
            if not self.main_chain.validate_transaction(legitimate_tx):
                return {"success": False, "error": "Insufficient balance for attack"}
            self.main_chain.add_transaction(legitimate_tx)
            self.record_event(f"Legitimate transaction: {attacker} -> {victim} ({amount} coins)")

            # Fork attacker chain
            self.attacker_chain = Blockchain("Attacker")
            self.attacker_chain.chain = [block for block in self.main_chain.chain]
            self.attacker_chain.balances = self.main_chain.balances.copy()

            double_spend_tx = Transaction(attacker, attacker, amount)
            self.attacker_chain.add_transaction(double_spend_tx)
            self.record_event(f"Double-spend transaction: {attacker} -> {attacker} ({amount} coins)")

            # Mine on main chain
            self.record_event("Mining on main chain...")
            self.main_chain.mine_block()

            if network_delay > 0:
                self.record_event(f"Simulating network delay of {network_delay}s")
                self.env.run(self.env.process(self._simulate_delay(network_delay)))

            self.record_event(f"{attacker} mining with {hash_rate}% hash power")
            self.attacker_chain.mine_block()
            self.attacker_chain.mine_block()

            success_probability = min(hash_rate / 100.0, 1.0) * (1.0 - min(network_delay / 10.0, 0.5))
            if random.random() > success_probability or (hash_rate / 100.0) < 0.5:
                self.record_event("Attack failed: Insufficient hash rate or too much delay")
                return {"success": False, "error": "Attack conditions not met", "event_records": self.event_records}

            self.record_event("Attack successful, broadcasting longer chain")
            self.main_chain = self.attacker_chain
            self.env.run(self.env.process(self.propagate_chain()))
            return {
                "success": True,
                "victim_loss": amount,
                "attacker_gain": amount,
                "event_records": self.event_records
            }
        except Exception as e:
            self.record_event(f"Attack failed: {str(e)}")
            return {"success": False, "error": str(e), "event_records": self.event_records}
        finally:
            self.attack_in_progress = False

    def _simulate_delay(self, delay):
        yield self.env.timeout(delay)

    def record_event(self, message):
        self.event_records.append({
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'message': message
        })

    def get_nodes_info(self):
        return [
            {'name': node['name'], 'hash_rate': node['hash_rate'],
             'balance': self.main_chain.balances.get(node['name'], 0)}
            for node in self.nodes
        ]

    def get_network_state(self):
        return {
            'main_chain': self.main_chain.to_dict(),
            'attack_in_progress': self.attack_in_progress,
            'event_records': self.event_records,
            'attack_chain': self.attacker_chain.to_dict() if self.attacker_chain else None
        }
