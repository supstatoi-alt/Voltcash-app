from flask import Flask, render_template_string, request, redirect, session, jsonify
from datetime import datetime
import hashlib
import os
import json
from decimal import Decimal
import secrets
import string

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'volt-cash-2026-super-secret-cm')

DATA_FILE = 'voltcash_data.json'

default_data = {
    'users': {},
    'agents': {},
    'transactions': [],
    'platform_balance': '0',
    'stats': {'total_deposits': 0, 'total_withdrawals': 0, 'total_users': 0, 'total_agents': 0}
}

def load_data():
    global users, agents, transactions, platform_balance, stats
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                users = {k: {**v, 'balance': Decimal(v['balance'])} for k, v in data.get('users', {}).items()}
                agents = {k: {**v, 'balance': Decimal(v['balance'])} for k, v in data.get('agents', {}).items()}
                transactions = data.get('transactions', [])
                platform_balance = Decimal(data.get('platform_balance', '0'))
                stats = data.get('stats', default_data['stats'])
        else:
            users = {}
            agents = {}
            transactions = []
            platform_balance = Decimal('0')
            stats = default_data['stats'].copy()
            save_data()
    except:
        users = {}
        agents = {}
        transactions = []
        platform_balance = Decimal('0')
        stats = default_data['stats'].copy()
        save_data()

def save_data():
    data = {
        'users': {k: {**v, 'balance': str(v['balance'])} for k, v in users.items()},
        'agents': {k: {**v, 'balance': str(v['balance'])} for k, v in agents.items()},
        'transactions': transactions[-100:],
        'platform_balance': str(platform_balance),
        'stats': stats
    }
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

load_data()

COMMISSIONS = {
    'depot': Decimal('0.02'),
    'retrait': Decimal('0.01'),
    'transfer': Decimal('0'),
    'agent_depot': Decimal('0.015'),
    'agent_retrait': Decimal('0.008')
}

ADMIN_EMAIL = 'admin@voltcash.cm'
ADMIN_PIN = '0000'

def generate_code():
    return 'VC' + ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))

def hash_pin(pin):
    return hashlib.sha256(pin.encode()).hexdigest()

def log_tx(user, action, amount, details='', fee=0):
    tx = {
        'user': user,
        'action': action,
        'amount': float(amount),
        'fee': float(fee),
        'details': details,
        'timestamp': datetime.now().isoformat()
    }
    transactions.insert(0, tx)
    save_data()
    return tx
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>⚡ VoltCash - Transferts Instantanés</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            color: white; min-height: 100vh; padding: 10px;
        }
        .container { 
            max-width: 450px; margin: 0 auto; background: rgba(20,20,40,0.95); 
            border-radius: 25px; padding: 30px; box-shadow: 0 20px 60px rgba(230,57,70,0.3);
        }
        h1 { color: #e63946; font-size: 2.5em; text-align: center; margin-bottom: 10px; font-weight: 900; }
        .subtitle { color: #ff6b6b; text-align: center; margin-bottom: 25px; font-size: 1.1em; }
        input, button { width: 100%; padding: 18px; margin: 12px 0; border-radius: 15px; font-size: 16px; }
        input { border: 2px solid rgba(230,57,70,0.3); background: rgba(50,50,70,0.8); color: white; }
        input:focus { border-color: #e63946; outline: none; }
        button { 
            background: linear-gradient(135deg, #e63946, #d63031); color: white; border: none; 
            font-weight: 700; cursor: pointer; text-transform: uppercase;
        }
        button:hover { transform: translateY(-3px); box-shadow: 0 15px 35px rgba(230,57,70,0.4); }
        .balance-card { 
            background: linear-gradient(135deg, #e63946, #ff6b6b); padding: 25px; 
            border-radius: 20px; margin: 25px 0; text-align: center;
        }
        .balance { font-size: 2.8em; font-weight: 900; }
        .status { padding: 15px; border-radius: 15px; margin: 15px 0; text-align: center; font-weight: 600; }
        .success { background: rgba(40,167,69,0.2); color: #90ee90; border: 2px solid #28a745; }
        .error { background: rgba(220,53,69,0.2); color: #ff8a80; border: 2px solid #dc3545; }
        .logout { 
            display: block; text-align: center; color: #ff6b6b; padding: 20px; 
            text-decoration: none; font-weight: 700;
        }
        hr { border: none; height: 2px; background: linear-gradient(90deg, transparent, #e63946, transparent); margin: 30px 0; }
    </style>
</head>
<body>
    <div class="container">
        {% if session.user %}
            <h1>⚡ VoltCash</h1>
            <div class="balance-card">
                <div style="font-size:1.2em;margin-bottom:10px">👋 {{ session.name }}</div>
                <div class="balance">{{ "%.0f"|format(session.balance) }} FCFA</div>
            </div>
            {% if success %}<div class="status success">{{ success|safe }}</div>{% endif %}
            {% if error %}<div class="status error">{{ error }}</div>{% endif %}
            
            <form method="POST">
                <input type="email" name="recipient" placeholder="📧 Email destinataire" required>
                <input type="number" name="amount" placeholder="​​​​​​​​​​​​​​​​
@app.route('/', methods=['GET', 'POST'])
def index():
    error = success = None
    
    if request.method == 'POST':
        action = request.form.get('action')
        email = request.form.get('email', '').lower().strip()
        pin = request.form.get('pin', '').strip()
        
        if action == 'register':
            if email in users:
                error = "❌ Compte existant"
            elif len(pin) != 4 or not pin.isdigit():
                error = "❌ PIN = 4 chiffres uniquement"
            else:
                code = generate_code()
                users[email] = {
                    'name': request.form.get('name', email),
                    'pin': hash_pin(pin),
                    'balance': Decimal('5000'),
                    'code': code,
                    'created': datetime.now().isoformat(),
                    'type': 'user'
                }
                log_tx(email, 'INSCRIPTION', 5000, f"Bonus + code {code}")
                stats['total_users'] = stats.get('total_users', 0) + 1
                save_data()
                session['user'] = email
                session['name'] = users[email]['name']
                session['balance'] = float(users[email]['balance'])
                success = f"✅ Compte créé ! Code: <strong>{code}</strong><br>💰 Bonus: 5 000 FCFA"
        
        elif action == 'login':
            if email == ADMIN_EMAIL and pin == ADMIN_PIN:
                session['user'] = email
                session['admin'] = True
                success = "✅ Admin connecté"
            elif email in users and users[email]['pin'] == hash_pin(pin):
                session['user'] = email
                session['admin'] = False
                session['name'] = users[email]['name']
                session['balance'] = float(users[email]['balance'])
                success = "✅ Connexion réussie"
            else:
                error = "❌ Email ou PIN incorrect"
        
        elif action == 'transfer' and 'user' in session:
            sender = session['user']
            recipient = request.form.get('recipient', '').lower().strip()
            try:
                amount = Decimal(request.form.get('amount', '0'))
            except:
                error = "❌ Montant invalide"
            
            if not error:
                if recipient not in users:
                    error = "❌ Destinataire introuvable"
                elif sender == recipient:
                    error = "❌ Pas à soi-même"
                elif users[sender]['balance'] < amount:
                    error = f"❌ Solde insuffisant (Besoin: {amount:,.0f} FCFA)"
                else:
                    users[sender]['balance'] -= amount
                    users[recipient]['balance'] += amount
                    session['balance'] = float(users[sender]['balance'])
                    log_tx(sender, 'TRANSFER', amount, f"→ {recipient}")
                    log_tx(recipient, 'REÇU', amount, f"← {sender}")
                    success = f"✅ {amount:,.0f} FCFA transférés !"
                    save_data()
    
    return render_template_string(HTML_TEMPLATE,
        session=session,
        users=users,
        transactions=transactions,
        platform_balance=float(platform_balance),
        stats=stats,
        success=success,
        error=error)
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
