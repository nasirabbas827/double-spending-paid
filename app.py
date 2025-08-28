
from flask import Flask, render_template, request, redirect, url_for, flash
from blockchain import Transaction, NetworkSimulator

app = Flask(__name__)
app.secret_key = 'blockchain_sim_2025'

# Initialize the network simulator
network = NetworkSimulator()

@app.route('/', methods=['GET'])
def index():
    """Display node information"""
    nodes = network.get_nodes_info()
    return render_template('index.html', nodes=nodes)

@app.route('/blockchain', methods=['GET'])
def blockchain():
    """Display blockchain and transaction details"""
    chain_info = network.get_network_state()
    return render_template('blockchain.html', chain=chain_info['main_chain']['chain'], 
                         pending_transactions=chain_info['main_chain']['pending_transactions'])

@app.route('/transactions', methods=['GET'])
def transactions():
    """Display transaction management page"""
    return render_template('transactions.html')

@app.route('/create_transaction', methods=['POST'])
def create_transaction():
    """Create and broadcast a new transaction"""
    try:
        sender = request.form['sender'].strip()
        recipient = request.form['recipient'].strip()
        amount = float(request.form['amount'])
        if amount <= 0:
            flash('Amount must be positive', 'error')
            return redirect(url_for('transactions'))
        transaction = Transaction(sender, recipient, amount)
        if network.broadcast_transaction(transaction):
            flash(f'Transaction created: {sender} -> {recipient} ({amount} coins)', 'success')
        else:
            flash(f'Transaction failed: Insufficient balance for {sender}', 'error')
    except ValueError:
        flash('Invalid amount format', 'error')
    except Exception as e:
        flash(str(e), 'error')
    return redirect(url_for('transactions'))

@app.route('/mine', methods=['POST'])
def mine_block():
    """Mine a new block on the main chain"""
    try:
        if network.main_chain.is_mining:
            flash('Mining already in progress', 'error')
            return redirect(url_for('transactions'))
        if not network.main_chain.pending_transactions:
            flash('No pending transactions to mine', 'error')
            return redirect(url_for('transactions'))
        result = network.main_chain.mine_block()
        if result:
            flash(f'Block mined: Block #{result["block"].index}, Time: {result["mining_time"]}s, Transactions: {result["transactions_count"]}', 'success')
            network.propagate_chain()
        else:
            flash('Mining failed', 'error')
    except Exception as e:
        flash(str(e), 'error')
    return redirect(url_for('transactions'))

@app.route('/attack', methods=['GET', 'POST'])
def attack():
    """Handle double-spending attack simulation"""
    if request.method == 'GET':
        nodes = network.get_nodes_info()
        return render_template(
            'attack.html',
            nodes=[n['name'] for n in nodes],
            event_records=network.get_network_state()['event_records'],
            attack_in_progress=network.get_network_state()['attack_in_progress']
        )

    try:
        attacker = request.form['attacker'].strip()
        victim = request.form['victim'].strip()
        amount = float(request.form['amount'])
        network_delay = float(request.form['network_delay'])
        hash_rate = float(request.form['hash_rate'])

        if attacker == victim:
            flash('Attacker and victim must be different nodes', 'error')
            return redirect(url_for('attack'))
        if amount <= 0:
            flash('Amount must be positive', 'error')
            return redirect(url_for('attack'))
        if network_delay < 0:
            flash('Network delay cannot be negative', 'error')
            return redirect(url_for('attack'))
        if hash_rate < 1 or hash_rate > 100:
            flash('Hash rate must be between 1 and 100', 'error')
            return redirect(url_for('attack'))

        attack_result = network.execute_attack(attacker, victim, amount, network_delay, hash_rate)
        if attack_result['success']:
            flash(
                f'Attack successful! Victim loss: {attack_result["victim_loss"]}, '
                f'Attacker gain: {attack_result["attacker_gain"]}',
                'success'
            )
        else:
            flash(f'Attack failed: {attack_result["error"]}', 'error')
    except ValueError:
        flash('Invalid input format', 'error')
    except Exception as e:
        flash(str(e), 'error')

    return redirect(url_for('attack'))


if __name__ == '__main__':
    print("Starting Blockchain Simulation")
    print("Dashboard: http://localhost:5000")
    print("Network initialized with 5 nodes")
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)