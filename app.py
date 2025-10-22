from flask import Flask, render_template, request, redirect, url_for, flash, send_file, send_from_directory
from blockchain import Transaction, NetworkSimulator
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Critical: Prevent GUI thread errors
import matplotlib.pyplot as plt
import os

app =  Flask(__name__)
app.secret_key = 'blockchain_sim_2025'

# Initialize simulator
network = NetworkSimulator()

# Ensure plots directory exists
os.makedirs('static/plots', exist_ok=True)


@app.route('/', methods=['GET'])
def index():
    nodes = network.get_nodes_info()
    return render_template('index.html', nodes=nodes)


@app.route('/blockchain', methods=['GET'])
def blockchain():
    chain_info = network.get_network_state()
    return render_template('blockchain.html',
                         chain=chain_info['main_chain']['chain'],
                         pending_transactions=chain_info['main_chain']['pending_transactions'])


@app.route('/transactions', methods=['GET'])
def transactions():
    return render_template('transactions.html')


@app.route('/create_transaction', methods=['POST'])
def create_transaction():
    try:
        sender = request.form['sender'].strip()
        recipient = request.form['recipient'].strip()
        amount = float(request.form['amount'])

        if sender == recipient:
            flash('Sender and recipient must be different', 'error')
            return redirect(url_for('transactions'))

        if amount <= 0:
            flash('Amount must be positive', 'error')
            return redirect(url_for('transactions'))

        transaction = Transaction(sender, recipient, amount)

        if network.broadcast_transaction(transaction):
            flash(f'Transaction created and verified: {sender} to {recipient} ({amount} coins)', 'success')
        else:
            flash(f'Transaction failed: Insufficient balance for {sender}', 'error')
    except ValueError:
        flash('Invalid amount format', 'error')
    except Exception as e:
        flash(f'Error creating transaction: {str(e)}', 'error')

    return redirect(url_for('transactions'))


@app.route('/mine', methods=['POST'])
def mine_block():
    try:
        if network.main_chain.is_mining:
            flash('Mining already in progress', 'error')
            return redirect(url_for('transactions'))

        if not network.main_chain.pending_transactions:
            flash('No pending transactions to mine', 'error')
            return redirect(url_for('transactions'))

        result = network.main_chain.mine_block()
        if result:
            flash(f'Block mined successfully! Block #{result["block"].index}, '
                  f'Time: {result["mining_time"]}s, '
                  f'Transactions: {result["transactions_count"]}', 'success')
            try:
                network.env.run(network.env.process(network.propagate_chain()))
            except Exception as e:
                print(f"Warning: Chain propagation had an issue: {e}")
        else:
            flash('Mining failed', 'error')
    except Exception as e:
        flash(f'Mining error: {str(e)}', 'error')

    return redirect(url_for('transactions'))


@app.route('/attack', methods=['GET', 'POST'])
def attack():
    if request.method == 'GET':
        nodes = network.get_nodes_info()
        state = network.get_network_state()
        return render_template(
            'attack.html',
            nodes=[n['name'] for n in nodes],
            event_records=state['event_records'],
            attack_in_progress=state['attack_in_progress']
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

        if not (1 <= hash_rate <= 100):
            flash('Hash rate must be between 1 and 100', 'error')
            return redirect(url_for('attack'))

        print("\n" + "="*60)
        print("INITIATING DOUBLE-SPENDING ATTACK")
        print("="*60)
        print(f"Attacker: {attacker}")
        print(f"Victim: {victim}")
        print(f"Amount: {amount} coins")
        print(f"Hash Rate: {hash_rate}%")
        print(f"Network Delay: {network_delay}s")
        print("="*60)

        attack_result = network.execute_attack(attacker, victim, amount, network_delay, hash_rate)

        if not attack_result:
            flash('Attack execution failed: No result returned', 'error')
            return redirect(url_for('attack'))

        if attack_result.get('success', False):
            flash(
                f'Attack SUCCESSFUL! {attacker} kept {attack_result["attacker_gain"]} coins. '
                f'{victim} lost {attack_result["victim_loss"]} coins. '
                f'Full details logged in terminal and attack_logs.csv.',
                'success'
            )
        else:
            flash(f'Attack FAILED: {attack_result.get("error", "Unknown reason")}. See terminal.', 'error')

    except ValueError as ve:
        flash(f'Invalid input format: {str(ve)}', 'error')
    except KeyError as ke:
        flash(f'Missing required field: {str(ke)}', 'error')
    except Exception as e:
        flash(f'Unexpected error during attack: {str(e)}', 'error')
        print(f"ERROR: {type(e).__name__}: {str(e)}")

    return redirect(url_for('attack'))


@app.route('/analytics', methods=['GET'])
def analytics():
    csv_path = 'attack_logs.csv'

    if not os.path.exists(csv_path):
        flash('No attack data available yet. Run some attacks first!', 'warning')
        return redirect(url_for('attack'))

    try:
        df = pd.read_csv(csv_path)
        print("CSV Columns:", df.columns.tolist())

        # Clean data
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
        df['Hash Rate (%)'] = pd.to_numeric(df['Hash Rate (%)'], errors='coerce')
        df['Network Delay (s)'] = pd.to_numeric(df['Network Delay (s)'], errors='coerce')
        df['Attack Result'] = df['Attack Result'].astype(str).str.strip()

        df = df.dropna(subset=['Amount', 'Hash Rate (%)', 'Network Delay (s)', 'Attack Result'])
        if df.empty:
            flash('No valid attack data to analyze.', 'warning')
            return redirect(url_for('attack'))

        plots_dir = 'static/plots'
        os.makedirs(plots_dir, exist_ok=True)

        # === 1. Success Rate vs Hash Rate ===
        plt.figure(figsize=(10, 6))
        bins = [0, 30, 40, 50, 60, 70, 80, 90, 100]
        df['Hash Rate Bin'] = pd.cut(df['Hash Rate (%)'], bins=bins, include_lowest=True)
        success_rate = df.groupby('Hash Rate Bin', observed=False)['Attack Result'].apply(
            lambda x: (x == 'Success').mean() * 100
        ).fillna(0)
        success_rate.plot(kind='bar', color='skyblue', edgecolor='navy')
        plt.title('Attack Success Rate by Hash Rate')
        plt.xlabel('Hash Rate (%)')
        plt.ylabel('Success Rate (%)')
        plt.xticks(rotation=45)
        plt.ylim(0, 100)
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(plots_dir, 'success_vs_hashrate.png'))
        plt.close()

        # === 2. Success Rate vs Network Delay ===
        plt.figure(figsize=(10, 6))
        bins_delay = [0, 1, 2, 3, 4, 5, 6, 10]
        df['Delay Bin'] = pd.cut(df['Network Delay (s)'], bins=bins_delay, include_lowest=True)
        success_by_delay = df.groupby('Delay Bin', observed=False)['Attack Result'].apply(
            lambda x: (x == 'Success').mean() * 100
        ).fillna(0)
        success_by_delay.plot(kind='bar', color='lightcoral', edgecolor='darkred')
        plt.title('Attack Success Rate by Network Delay')
        plt.xlabel('Network Delay (seconds)')
        plt.ylabel('Success Rate (%)')
        plt.xticks(rotation=45)
        plt.ylim(0, 100)
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(plots_dir, 'success_vs_delay.png'))
        plt.close()

        # === 3. Amount Distribution ===
        plt.figure(figsize=(10, 6))
        success = df[df['Attack Result'] == 'Success']['Amount'].dropna()
        failed = df[df['Attack Result'] == 'Failed']['Amount'].dropna()
        if not success.empty or not failed.empty:
            plt.hist([success, failed], bins=10, label=['Success', 'Failed'],
                     color=['green', 'red'], alpha=0.7)
        plt.title('Distribution of Attack Amounts')
        plt.xlabel('Amount (coins)')
        plt.ylabel('Number of Attacks')
        plt.legend()
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(plots_dir, 'amount_distribution.png'))
        plt.close()

        # === 4. Cumulative Attacks ===
        df['Attack Timestamp'] = pd.to_datetime(df['Attack Timestamp'], errors='coerce')
        df_sorted = df.sort_values('Attack Timestamp').dropna(subset=['Attack Timestamp'])
        if not df_sorted.empty:
            df_sorted['Cumulative Attacks'] = range(1, len(df_sorted) + 1)
            df_sorted['Cumulative Success'] = (df_sorted['Attack Result'] == 'Success').cumsum()
            plt.figure(figsize=(12, 6))
            plt.plot(df_sorted['Attack Timestamp'], df_sorted['Cumulative Attacks'],
                     label='Total Attacks', marker='o', linewidth=2)
            plt.plot(df_sorted['Attack Timestamp'], df_sorted['Cumulative Success'],
                     label='Successful Attacks', marker='o', color='green', linewidth=2)
            plt.title('Cumulative Attack Attempts Over Time')
            plt.xlabel('Time')
            plt.ylabel('Count')
            plt.legend()
            plt.grid(alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(os.path.join(plots_dir, 'cumulative_attacks.png'))
            plt.close()
        else:
            plt.figure(figsize=(12, 6))
            plt.text(0.5, 0.5, 'No valid timestamps', ha='center', va='center', transform=plt.gca().transAxes)
            plt.axis('off')
            plt.savefig(os.path.join(plots_dir, 'cumulative_attacks.png'))
            plt.close()

        # Summary
        total_attacks = len(df)
        success_count = len(df[df['Attack Result'] == 'Success'])
        success_rate = (success_count / total_attacks * 100) if total_attacks > 0 else 0
        avg_hash_success = df[df['Attack Result'] == 'Success']['Hash Rate (%)'].mean()
        avg_delay_failed = df[df['Attack Result'] == 'Failed']['Network Delay (s)'].mean()

        summary = {
            'total_attacks': total_attacks,
            'success_count': success_count,
            'success_rate': round(success_rate, 2),
            'avg_hash_success': round(avg_hash_success, 2) if pd.notna(avg_hash_success) else 0,
            'avg_delay_failed': round(avg_delay_failed, 2) if pd.notna(avg_delay_failed) else 0,
        }

        return render_template(
            'analytics.html',
            summary=summary,
            plots={
                'success_vs_hashrate': 'success_vs_hashrate.png',
                'success_vs_delay': 'success_vs_delay.png',
                'amount_distribution': 'amount_distribution.png',
                'cumulative_attacks': 'cumulative_attacks.png'
            },
            csv_path=csv_path
        )

    except Exception as e:
        flash(f'Error generating analytics: {str(e)}', 'error')
        print(f"Analytics Error: {e}")
        return redirect(url_for('attack'))


@app.route('/plots/<path:filename>')
def serve_plots(filename):
    return send_from_directory('static/plots', filename)


@app.route('/download_csv')
def download_csv():
    csv_path = 'attack_logs.csv'
    if os.path.exists(csv_path):
        return send_file(csv_path, as_attachment=True, download_name='attack_logs_full.csv')
    else:
        flash('CSV file not found!', 'error')
        return redirect(url_for('attack'))


if __name__ == '__main__':
    print("\n" + "="*60)
    print("BLOCKCHAIN DOUBLE-SPENDING ATTACK SIMULATOR")
    print("="*60)
    print("Dashboard: http://localhost:5000")
    print("Network initialized with 6 nodes")
    print("Nodes: Node1, Node2, Node3, Node4, Node5, Node6")
    print("\nFeatures:")
    print("  - Transaction verification by all 6 nodes")
    print("  - Double-spending attack simulation")
    print("  - Private chain mining")
    print("  - Detailed terminal logs")
    print("  - CSV attack logging (attack_logs.csv) with full block JSON")
    print("  - Analytics Dashboard with Matplotlib + Pandas")
    print("="*60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)