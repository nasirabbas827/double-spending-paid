import hashlib
import json
import time
import random
from datetime import datetime
import uuid
import simpy
import csv
import os

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
        self.balances = {
            'Node1': 100, 'Node2': 100, 'Node3': 100,
            'Node4': 100, 'Node5': 100, 'Node6': 100
        }
        self.is_mining = False

    def create_genesis_block(self):
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
        self.balances = {
            'Node1': 100, 'Node2': 100, 'Node3': 100,
            'Node4': 100, 'Node5': 100, 'Node6': 100
        }
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
        self.nodes = [
            {'name': 'Node1', 'hash_rate': 0.20},
            {'name': 'Node2', 'hash_rate': 0.18},
            {'name': 'Node3', 'hash_rate': 0.17},
            {'name': 'Node4', 'hash_rate': 0.15},
            {'name': 'Node5', 'hash_rate': 0.15},
            {'name': 'Node6', 'hash_rate': 0.15}
        ]
        self.network = simpy.Store(self.env, capacity=float('inf'))
        self.csv_filename = 'attack_logs.csv'
        self.initialize_csv()

    def initialize_csv(self):
        """Initialize CSV file with enhanced headers"""
        if not os.path.exists(self.csv_filename):
            with open(self.csv_filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'Attack Timestamp',
                    'Public Tx ID',
                    'Public Sender',
                    'Public Receiver',
                    'Amount',
                    'Public Block Index',
                    'Public Previous Hash',
                    'Public Current Hash',
                    'Public Timestamp',
                    'Public Nonce',
                    'Public Transactions JSON',
                    'Private Tx ID',
                    'Private Sender',
                    'Private Receiver',
                    'Private Block Index',
                    'Private Previous Hash',
                    'Private Current Hash',
                    'Private Timestamp',
                    'Private Nonce',
                    'Private Transactions JSON',
                    'Hash Rate (%)',
                    'Network Delay (s)',
                    'Attack Result'
                ])

    def log_attack_to_csv(self, public_tx, private_tx, attack_result, hash_rate, network_delay, public_block=None, private_block=None):
        """Log full attack details with correct block containing the transaction"""
        # Find the block that contains the public_tx
        public_details_block = public_block
        if not public_details_block:
            for block in reversed(self.main_chain.chain):
                if any(tx.transaction_id == public_tx.transaction_id for tx in block.transactions):
                    public_details_block = block
                    break
            else:
                public_details_block = self.main_chain.chain[-1] if self.main_chain.chain else None

        # Find the block that contains the private_tx
        private_details_block = private_block
        if not private_details_block and self.attacker_chain:
            for block in reversed(self.attacker_chain.chain):
                if any(tx.transaction_id == private_tx.transaction_id for tx in block.transactions):
                    private_details_block = block
                    break
            else:
                private_details_block = self.attacker_chain.chain[-1] if self.attacker_chain.chain else None

        with open(self.csv_filename, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            def get_block_info(block):
                if not block:
                    return {k: 'N/A' for k in ['index', 'previous_hash', 'hash', 'timestamp', 'nonce', 'transactions']}
                return {
                    'index': block.index,
                    'previous_hash': block.previous_hash[:64] + '...' if len(block.previous_hash) > 64 else block.previous_hash,
                    'hash': block.hash,
                    'timestamp': datetime.fromtimestamp(block.timestamp).strftime('%Y-%m-%d %H:%M:%S'),
                    'nonce': block.nonce,
                    'transactions': [tx.to_dict() for tx in block.transactions]
                }

            pub_info = get_block_info(public_details_block)
            pri_info = get_block_info(private_details_block)

            writer.writerow([
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                public_tx.transaction_id,
                public_tx.sender,
                public_tx.recipient,
                public_tx.amount,
                pub_info['index'],
                pub_info['previous_hash'],
                pub_info['hash'],
                pub_info['timestamp'],
                pub_info['nonce'],
                json.dumps(pub_info['transactions'], indent=2),
                private_tx.transaction_id,
                private_tx.sender,
                private_tx.recipient,
                pri_info['index'],
                pri_info['previous_hash'],
                pri_info['hash'],
                pri_info['timestamp'],
                pri_info['nonce'],
                json.dumps(pri_info['transactions'], indent=2),
                hash_rate,
                network_delay,
                "Success" if attack_result else "Failed"
            ])

    def broadcast_transaction(self, transaction):
        self.env.process(self._broadcast_transaction(transaction))
        print(f"\n{'='*60}")
        print(f"Broadcasting Transaction: {transaction.transaction_id}")
        print(f"{'='*60}")
        verified_by = []
        for node in self.nodes:
            if self.main_chain.validate_transaction(transaction):
                verified_by.append(node['name'])
                print(f"{node['name']}: Transaction VERIFIED")
            else:
                print(f"{node['name']}: Transaction REJECTED (Insufficient balance)")
        if len(verified_by) >= 4:
            result = self.main_chain.add_transaction(transaction)
            print(f"\nTransaction ACCEPTED by network ({len(verified_by)}/6 nodes)")
            return result
        else:
            print(f"\nTransaction REJECTED by network (Only {len(verified_by)}/6 nodes verified)")
            return False

    def _broadcast_transaction(self, transaction):
        yield self.env.timeout(0.1)
        self.network.put(('transaction', transaction))

    def propagate_chain(self):
        yield self.env.timeout(0.1)
        self.record_event("Chain propagated to all 6 nodes")

    def execute_attack(self, attacker, victim, amount, network_delay, hash_rate):
        if self.attack_in_progress:
            return {
                "success": False,
                "error": "Another attack is already in progress. Please wait for it to complete.",
                "event_records": []
            }
        self.attack_in_progress = True
        self.event_records = []
        try:
            self.record_event(f"Double-Spending Attack Initiated by {attacker}")
            print(f"\n{'='*60}")
            print("DOUBLE-SPENDING ATTACK INITIATED")
            print(f"{'='*60}")
            print(f"Attacker: {attacker}")
            print(f"Victim: {victim}")
            print(f"Amount: {amount} coins")
            print(f"Hash Rate: {hash_rate}%")
            print(f"Network Delay: {network_delay}s")
            if not self.main_chain.validate_transaction(Transaction(attacker, victim, amount)):
                error_msg = f"{attacker} has insufficient balance ({self.main_chain.balances.get(attacker, 0)} coins) for transaction of {amount} coins"
                self.record_event(f"Attack Failed: {error_msg}")
                print(f"\nAttack Failed: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "event_records": self.event_records
                }
            public_tx = Transaction(attacker, victim, amount)
            private_tx = Transaction(attacker, attacker, amount)
            print(f"\n{'='*60}")
            print("SIMULTANEOUS TRANSACTIONS INITIATED")
            print(f"{'='*60}")
            print("PUBLIC Transaction (broadcast to network):")
            print(f" - ID: {public_tx.transaction_id}")
            print(f" - From: {public_tx.sender} to {public_tx.recipient}")
            print(f" - Amount: {public_tx.amount} coins")
            print(f" - Timestamp: {datetime.fromtimestamp(public_tx.timestamp).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f" - Hash: {public_tx.calculate_hash()}")
            print("\nPRIVATE Transaction (on attacker's secret chain):")
            print(f" - ID: {private_tx.transaction_id}")
            print(f" - From: {private_tx.sender} to {private_tx.recipient}")
            print(f" - Amount: {private_tx.amount} coins")
            print(f" - Timestamp: {datetime.fromtimestamp(private_tx.timestamp).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f" - Hash: {private_tx.calculate_hash()}")
            self.record_event(f"Public Transaction: {attacker} to {victim} ({amount} coins)")
            self.main_chain.add_transaction(public_tx)
            self.attacker_chain = Blockchain("Attacker_Private")
            self.attacker_chain.chain = [block for block in self.main_chain.chain]
            self.attacker_chain.balances = self.main_chain.balances.copy()
            self.record_event(f"Private Transaction: {attacker} to {attacker} ({amount} coins) [Secret Chain]")
            self.attacker_chain.add_transaction(private_tx)
            print(f"\n{'='*60}")
            print("PUBLIC CHAIN MINING")
            print(f"{'='*60}")
            self.record_event("Honest nodes mining public transaction...")
            public_result = self.main_chain.mine_block()
            public_mined_block = public_result['block'] if public_result else None
            if public_mined_block:
                print(f"Public chain mined block #{public_mined_block.index}")
                print(f" - Mining time: {public_result['mining_time']}s")
                print(f" - Transactions: {public_result['transactions_count']}")
                self.record_event(f"Public chain: Block #{public_mined_block.index} mined")
            else:
                public_mined_block = self.main_chain.chain[-1]  # fallback
            if network_delay > 0:
                print(f"\nNetwork delay: {network_delay}s")
                self.record_event(f"Network delay: {network_delay}s")
                self.env.run(self.env.process(self._simulate_delay(network_delay)))
            print(f"\n{'='*60}")
            print("PRIVATE CHAIN MINING (SECRET)")
            print(f"{'='*60}")
            print(f"{attacker} mining with {hash_rate}% hash power...")
            self.record_event(f"{attacker} mining private chain with {hash_rate}% hash power")
            # Mine first private block (with private_tx)
            private_result1 = self.attacker_chain.mine_block()
            private_mined_block1 = private_result1['block'] if private_result1 else None
            if private_mined_block1:
                print(f"Private chain mined block #{private_mined_block1.index}")
                self.record_event(f"Private chain: Block #{private_mined_block1.index} mined")
            # Mine second block
            private_result2 = self.attacker_chain.mine_block()
            private_mined_block2 = private_result2['block'] if private_result2 else None
            if private_mined_block2:
                print(f"Private chain mined block #{private_mined_block2.index}")
                self.record_event(f"Private chain: Block #{private_mined_block2.index} mined")
            if hash_rate >= 51:
                print(f"{attacker} mining DUMMY block to extend private chain...")
                dummy_block = Block(
                    index=len(self.attacker_chain.chain),
                    transactions=[],
                    timestamp=time.time(),
                    previous_hash=self.attacker_chain.get_latest_block().hash
                )
                dummy_time = dummy_block.mine_block(self.attacker_chain.difficulty)
                self.attacker_chain.chain.append(dummy_block)
                print(f"Private chain mined DUMMY block #{dummy_block.index} (no tx)")
                self.record_event(f"Private chain: DUMMY Block #{dummy_block.index} mined")
            honest_power = max(0.1, (100 - hash_rate) / 100.0)
            if random.random() < honest_power:
                print("Honest nodes mining second block...")
                honest_result = self.main_chain.mine_block()
                if honest_result:
                    print(f"Honest chain mined block #{honest_result['block'].index}")
                    self.record_event(f"Honest chain: Block #{honest_result['block'].index} mined")
            public_length = len(self.main_chain.chain)
            private_length = len(self.attacker_chain.chain)
            print(f"\nChain Length Comparison:")
            print(f" Public Chain: {public_length} blocks")
            print(f" Private Chain: {private_length} blocks")
            attack_successful = False
            failure_reason = ""
            if private_length > public_length:
                attack_successful = True
                print(f"\n{'='*60}")
                print("ATTACK SUCCESSFUL!")
                print(f"{'='*60}")
                print("Private chain is LONGER to Re-org happening...")
                self.record_event("Attack SUCCESSFUL: Private chain is longer!")
                self.record_event("Broadcasting longer private chain to network...")
                self.main_chain = self.attacker_chain
                self.env.run(self.env.process(self.propagate_chain()))
                print("Network accepted private chain")
                print(f"{attacker} kept {amount} coins")
                print(f"{victim} received nothing (transaction reversed)")
                self.record_event(f"{attacker} successfully kept {amount} coins")
                self.record_event(f"{victim} lost {amount} coins")
            else:
                if hash_rate < 51:
                    failure_reason = f"Insufficient hash rate ({hash_rate}%). Need >50%."
                else:
                    failure_reason = f"Private chain not longer (Public: {public_length}, Private: {private_length})."
                print(f"\n{'='*60}")
                print("ATTACK FAILED")
                print(f"{'='*60}")
                print(f"Reason: {failure_reason}")
                self.record_event(f"Attack FAILED: {failure_reason}")
                self.record_event(f"{victim} successfully received {amount} coins")
            # Use the actual mined blocks that contain the transactions
            self.log_attack_to_csv(
                public_tx, private_tx, attack_successful, hash_rate, network_delay,
                public_block=public_mined_block,
                private_block=private_mined_block1  # first private block contains the tx
            )
            print(f"\nAttack details logged to {self.csv_filename}")
            return {
                "success": attack_successful,
                "victim_loss": amount if attack_successful else 0,
                "attacker_gain": amount if attack_successful else 0,
                "public_transaction": public_tx.to_dict(),
                "private_transaction": private_tx.to_dict(),
                "event_records": self.event_records,
                "error": None if attack_successful else failure_reason
            }
        except Exception as e:
            error_msg = f"System error during attack execution: {str(e)}"
            self.record_event(f"Attack failed: {error_msg}")
            print(f"\nError during attack: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "event_records": self.event_records
            }
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