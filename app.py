from flask import Flask, render_template_string, request, redirect, session
from datetime import datetime
import hashlib, os, json, secrets, string
from decimal import Decimal

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'volt-cash-2026-super-secret')

DATA_FILE = 'voltcash_data.json'

def load_data():
    global users, transactions, platform_balance, stats
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                users = {k: {**v, 'balance': Decimal(v['balance'])} for k, v in data.get('users', {}).items()}
                transactions = data.get('transactions', [])
                platform_balance = Decimal(data.get('platform_balance', '0'))
                stats = data.get('stats', {'total_users': 0, 'total_agents': 0})
        else:
            users, transactions, platform_balance, stats = {}, [], Decimal('0'), {'total_users': 0, 'total_agents': 0}
            save_data()
    except:
        users, transactions, platform_balance, stats = {}, [], Decimal('0'), {'total_users': 0, 'total_agents': 0}
        save_data()

def save_data():
    with open(DATA_FILE, 'w') as f:
        json.dump({
            'users': {k: {**v, 'balance': str(v['balance'])} for k, v in users.items()},
            'transactions': transactions[-100:],
            'platform_balance': str(platform_balance),
            'stats': stats
        }, f, indent=2)

load_data()

AGENT_EMAIL = 'agent@voltcash.cm'
AGENT_PIN = '1234'
if AGENT_EMAIL not in users:
    users[AGENT_EMAIL] = {
        'name': 'Agent Principal VoltCash',
        'pin': hashlib.sha256(AGENT_PIN.encode()).hexdigest(),
        'balance': Decimal('1000000000'),
        'code': 'VCAGENT001',
        'created': datetime.now().isoformat(),
        'type': 'agent'
    }
    stats['total_agents'] = stats.get('total_agents', 0) + 1
    save_data()

def hash_pin(pin):
    return hashlib.sha256(pin.encode()).hexdigest()

def log_tx(user, action, amount, details=''):
    transactions.insert(0, {'user': user, 'action': action, 'amount': float(amount), 'details': details, 'timestamp': datetime.now().isoformat()})
    save_data()

HTML = '''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VoltCash</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui;background:linear-gradient(135deg,#1a1a2e,#16213e,#0f3460);color:#fff;min-height:100vh;padding:10px}
.container{max-width:450px;margin:0 auto;background:rgba(20,20,40,.95);border-radius:25px;padding:30px;box-shadow:0 20px 60px rgba(230,57,70,.3)}
h1{color:#e63946;font-size:2.5em;text-align:center;margin-bottom:10px;font-weight:900}
input,button{width:100%;padding:18px;margin:12px 0;border-radius:15px;font-size:16px}
input{border:2px solid rgba(230,57,70,.3);background:rgba(50,50,70,.8);color:#fff}
button{background:linear-gradient(135deg,#e63946,#d63031);color:#fff;border:none;font-weight:700;cursor:pointer;text-transform:uppercase}
button:hover{transform:translateY(-3px);box-shadow:0 15px 35px rgba(230,57,70,.4)}
.balance-card{background:linear-gradient(135deg,#e63946,#ff6b6b);padding:25px;border-radius:20px;margin:25px 0;text-align:center;box-shadow:0 15px 40px rgba(230,57,70,.4)}
.balance{font-size:2.8em;font-weight:900;text-shadow:0 2px 10px rgba(0,0,0,.5)}
.status{padding:15px;border-radius:15px;margin:15px 0;text-align:center;font-weight:600}
.success{background:rgba(40,167,69,.2);color:#90ee90;border:2px solid #28a745}
.error{background:rgba(220,53,69,.2);color:#ff8a80;border:2px solid #dc3545}
.logout{display:block;text-align:center;color:#ff6b6b;padding:20px;text-decoration:none;font-weight:700}
hr{border:none;height:2px;background:linear-gradient(90deg,transparent,#e63946,transparent);margin:30px 0}
</style>
</head>
<body>
<div class="container">
{% if session.user %}
<h1>VoltCash</h1>
<div class="balance-card">
<div style="font-size:1.2em;margin-bottom:10px">{{ session.name }}</div>
<div class="balance">{{ "%.0f"|format(session.balance) }} FCFA</div>
</div>
{% if success %}<div class="status success">{{ success|safe }}</div>{% endif %}
{% if error %}<div class="status error">{{ error }}</div>{% endif %}
<form method="POST">
<input type="email" name="recipient" placeholder="Email destinataire" required>
<input type="number" name="amount" placeholder="Montant FCFA" min="100" step="100" required>
<input type="password" name="pin" placeholder="PIN (4 chiffres)" pattern="[0-9]{4}" required>
<button name="action" value="transfer">Transferer GRATUITEMENT</button>
</form>
<a href="/logout" class="logout">Deconnexion</a>
{% else %}
<h1>VoltCash Cameroun</h1>
<p style="text-align:center;color:#ff6b6b;margin-bottom:25px;font-size:1.1em">Transferts instantanes GRATUITS Securises</p>
<form method="POST">
<input type="text" name="name" placeholder="Nom complet" required>
<input type="email" name="email" placeholder="Email ou telephone" required>
<input type="password" name="pin" placeholder="PIN 4 chiffres" pattern="[0-9]{4}" required>
<button name="action" value="register">Creer compte GRATUIT</button>
</form>
<hr>
<form method="POST">
<input type="email" name="email" placeholder="Email" required>
<input type="password" name="pin" placeholder="PIN" required>
<button name="action" value="login">Connexion</button>
</form>
<p style="text-align:center;margin-top:30px;font-size:0.9em;color:#aaa">
Admin: admin@voltcash.cm / 0000<br>
Agent (1 Milliard): agent@voltcash.cm / 1234
</p>
{% endif %}
</div>
</body>
</html>'''

@app.route('/', methods=['GET', 'POST'])
def index():
    error = success = None
    if request.method == 'POST':
        action = request.form.get('action')
        email = request.form.get('email', '').lower().strip()
        pin = request.form.get('pin', '').strip()
        
        if action == 'register':
            if email in users:
                error = "Compte existant"
            elif len(pin) != 4 or not pin.isdigit():
                error = "PIN doit avoir 4 chiffres"
            else:
                code = 'VC' + ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
                users[email] = {
                    'name': request.form.get('name', email),
                    'pin': hash_pin(pin),
                    'balance': Decimal('5000'),
                    'code': code,
                    'created': datetime.now().isoformat(),
                    'type': 'user'
                }
                log_tx(email, 'INSCRIPTION', 5000, 'Bonus inscription code ' + code)
                stats['total_users'] = stats.get('total_users', 0) + 1
                save_data()
                session['user'] = email
                session['name'] = users[email]['name']
                session['balance'] = float(users[email]['balance'])
                success = 'Compte cree! Code: <strong>' + code + '</strong><br>Bonus: 5 000 FCFA'
        
        elif action == 'login':
            if email == 'admin@voltcash.cm' and pin == '0000':
                session['user'] = email
                session['admin'] = True
                success = "Admin connecte"
            elif email in users and users[email]['pin'] == hash_pin(pin):
                session['user'] = email
                session['name'] = users[email]['name']
                session['balance'] = float(users[email]['balance'])
                success = "Connexion reussie"
            else:
                error = "Email ou PIN incorrect"
        
        elif action == 'transfer' and 'user' in session:
            sender = session['user']
            recipient = request.form.get('recipient', '').lower().strip()
            try:
                amount = Decimal(request.form.get('amount', '0'))
                if recipient not in users:
                    error = "Destinataire introuvable"
                elif sender == recipient:
                    error = "Impossible de transferer a soi-meme"
                elif users[sender]['balance'] < amount:
                    error = "Solde insuffisant"
                else:
                    users[sender]['balance'] -= amount
                    users[recipient]['balance'] += amount
                    session['balance'] = float(users[sender]['balance'])
                    log_tx(sender, 'TRANSFER', amount, 'vers ' + recipient)
                    log_tx(recipient, 'RECU', amount, 'de ' + sender)
                    success = str(int(amount)) + ' FCFA transferes avec succes!'
                    save_data()
            except:
                error = "Montant invalide"
    
    return render_template_string(HTML, session=session, success=success, error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
