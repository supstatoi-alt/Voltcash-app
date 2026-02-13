from flask import Flask, render_template_string, request, redirect, session, jsonify, send_file
from datetime import datetime
import hashlib, os, json, secrets, string, io
from decimal import Decimal
from collections import defaultdict

try:
import qrcode
except:
qrcode = None

app = Flask(**name**)
app.secret_key = os.environ.get(‘SECRET_KEY’, ‘volt-cash-premium-2026-secret-key’)

DATA_FILE = ‘voltcash_data.json’

def load_data():
global users, agents, transactions, platform_balance, stats, payment_requests
try:
if os.path.exists(DATA_FILE):
with open(DATA_FILE, ‘r’) as f:
data = json.load(f)
users = {k: {**v, ‘balance’: Decimal(v[‘balance’])} for k, v in data.get(‘users’, {}).items()}
agents = {k: {**v, ‘balance’: Decimal(v[‘balance’])} for k, v in data.get(‘agents’, {}).items()}
transactions = data.get(‘transactions’, [])
platform_balance = Decimal(data.get(‘platform_balance’, ‘0’))
stats = data.get(‘stats’, {‘total_users’: 0, ‘total_agents’: 0, ‘total_deposits’: 0, ‘total_withdrawals’: 0})
payment_requests = data.get(‘payment_requests’, [])
else:
users, agents, transactions = {}, {}, []
platform_balance = Decimal(‘0’)
stats = {‘total_users’: 0, ‘total_agents’: 0, ‘total_deposits’: 0, ‘total_withdrawals’: 0}
payment_requests = []
save_data()
except:
users, agents, transactions = {}, {}, []
platform_balance = Decimal(‘0’)
stats = {‘total_users’: 0, ‘total_agents’: 0, ‘total_deposits’: 0, ‘total_withdrawals’: 0}
payment_requests = []
save_data()

def save_data():
with open(DATA_FILE, ‘w’) as f:
json.dump({
‘users’: {k: {**v, ‘balance’: str(v[‘balance’])} for k, v in users.items()},
‘agents’: {k: {**v, ‘balance’: str(v[‘balance’])} for k, v in agents.items()},
‘transactions’: transactions[-500:],
‘platform_balance’: str(platform_balance),
‘stats’: stats,
‘payment_requests’: payment_requests[-100:]
}, f, indent=2)

load_data()

COMMISSIONS = {
‘depot’: Decimal(‘0.02’),
‘retrait’: Decimal(‘0.01’),
‘transfer’: Decimal(‘0’),
‘agent_depot’: Decimal(‘0.015’),
‘agent_retrait’: Decimal(‘0.008’)
}

AGENT_EMAIL = ‘agent@voltcash.cm’
AGENT_PIN = ‘1234’
if AGENT_EMAIL not in users:
users[AGENT_EMAIL] = {
‘name’: ‘Agent Principal VoltCash’,
‘pin’: hashlib.sha256(AGENT_PIN.encode()).hexdigest(),
‘balance’: Decimal(‘1000000000’),
‘code’: ‘VCAGENT001’,
‘created’: datetime.now().isoformat(),
‘type’: ‘agent’,
‘phone’: ‘+237600000000’,
‘theme’: ‘light’
}
stats[‘total_agents’] = 1
save_data()

ADMIN_EMAIL = ‘admin@voltcash.cm’
ADMIN_PIN = ‘0000’

def hash_pin(pin):
return hashlib.sha256(pin.encode()).hexdigest()

def generate_code():
return ‘VC’ + ‘’.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))

def log_tx(user, action, amount, details=’’, fee=0, recipient=’’):
tx = {
‘id’: ‘TX’ + secrets.token_hex(8).upper(),
‘user’: user,
‘action’: action,
‘amount’: float(amount),
‘fee’: float(fee),
‘details’: details,
‘recipient’: recipient,
‘timestamp’: datetime.now().isoformat(),
‘status’: ‘completed’
}
transactions.insert(0, tx)
save_data()
return tx

def get_user_transactions(email, limit=50):
return [t for t in transactions if t[‘user’] == email or t.get(‘recipient’) == email][:limit]

def get_monthly_stats(email):
monthly = defaultdict(lambda: {‘sent’: 0, ‘received’: 0})
for tx in get_user_transactions(email, limit=200):
try:
tx_date = datetime.fromisoformat(tx[‘timestamp’])
month_key = tx_date.strftime(’%m’)
if tx[‘user’] == email and tx[‘action’] in [‘TRANSFER’, ‘RETRAIT’]:
monthly[month_key][‘sent’] += tx[‘amount’]
elif tx.get(‘recipient’) == email or tx[‘action’] == ‘RECU’:
monthly[month_key][‘received’] += tx[‘amount’]
except:
pass
return [{‘month’: k, ‘sent’: v[‘sent’], ‘received’: v[‘received’]} for k, v in sorted(monthly.items())[-6:]]

HTML_TEMPLATE = ‘’’<!DOCTYPE html>

<html lang="fr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#003087"><title>💎 VoltCash Premium</title>
<style>:root{--primary:#003087;--primary-light:#009CDE;--success:#28a745;--danger:#dc3545;--bg:#f5f7fa;--card:#fff;--text:#2c3e50;--border:#e1e8ed}[data-theme=dark]{--primary:#009CDE;--bg:#0a0e27;--card:#1a1f3a;--text:#e4e6eb;--border:#2d3748}*{box-sizing:border-box;margin:0;padding:0}body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;background:var(--bg);color:var(--text);transition:all .3s}.app{max-width:480px;margin:0 auto;min-height:100vh;background:var(--card)}.header{background:linear-gradient(135deg,var(--primary),var(--primary-light));color:#fff;padding:20px;border-radius:0 0 30px 30px;box-shadow:0 10px 30px rgba(0,48,135,.2)}.header-top{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}.header-top h1{font-size:24px;font-weight:700}.theme-btn{background:rgba(255,255,255,.2);border:none;color:#fff;padding:8px 12px;border-radius:20px;cursor:pointer;font-size:18px}.balance{text-align:center;padding:30px 0}.balance-label{font-size:14px;opacity:.9;margin-bottom:5px}.balance-amount{font-size:48px;font-weight:900;text-shadow:0 2px 10px rgba(0,0,0,.2)}.actions{display:grid;grid-template-columns:repeat(4,1fr);gap:15px;padding:20px;margin-top:-30px}.action-btn{background:var(--card);border:none;border-radius:20px;padding:20px 10px;text-align:center;cursor:pointer;box-shadow:0 5px 20px rgba(0,0,0,.1);transition:all .3s;text-decoration:none;color:var(--text)}.action-btn:hover{transform:translateY(-5px);box-shadow:0 10px 30px rgba(0,0,0,.15)}.action-btn .icon{font-size:28px;margin-bottom:5px}.action-btn .label{font-size:12px;font-weight:600}.card{background:var(--card);border-radius:20px;padding:20px;margin:15px;box-shadow:0 2px 10px rgba(0,0,0,.05);border:1px solid var(--border)}.card-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:15px}.card-title{font-size:18px;font-weight:700}.card-action{background:0 0;border:none;color:var(--primary);cursor:pointer;font-size:14px;font-weight:600;text-decoration:none}.chart{height:150px;display:flex;align-items:flex-end;justify-content:space-around;margin-top:20px}.chart-bar{width:30px;background:linear-gradient(to top,var(--primary),var(--primary-light));border-radius:10px 10px 0 0;transition:all .3s;cursor:pointer}.chart-label{text-align:center;font-size:11px;margin-top:5px}.tx-list{max-height:400px;overflow-y:auto}.tx-item{display:flex;align-items:center;padding:15px;border-bottom:1px solid var(--border);transition:background .2s}.tx-item:hover{background:var(--bg)}.tx-item:last-child{border-bottom:none}.tx-icon{width:45px;height:45px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:20px;margin-right:15px}.tx-icon.sent{background:#fee;color:var(--danger)}.tx-icon.received{background:#efe;color:var(--success)}.tx-icon.deposit{background:#eff;color:var(--primary)}.tx-details{flex:1}.tx-name{font-weight:600;font-size:15px;margin-bottom:3px}.tx-date{font-size:13px;color:#888}.tx-amount{font-size:16px;font-weight:700}.tx-amount.positive{color:var(--success)}.tx-amount.negative{color:var(--danger)}input,select,textarea{width:100%;padding:15px;margin:10px 0;border:2px solid var(--border);border-radius:15px;font-size:16px;background:var(--card);color:var(--text);transition:all .3s;font-family:inherit}input:focus,select:focus,textarea:focus{border-color:var(--primary);outline:0;box-shadow:0 0 0 3px rgba(0,48,135,.1)}.btn{width:100%;padding:18px;margin:15px 0;background:linear-gradient(135deg,var(--primary),var(--primary-light));color:#fff;border:none;border-radius:15px;font-size:16px;font-weight:700;cursor:pointer;transition:all .3s;text-transform:uppercase;letter-spacing:.5px}.btn:hover{transform:translateY(-2px);box-shadow:0 10px 30px rgba(0,48,135,.3)}.btn-secondary{background:linear-gradient(135deg,#6c757d,#5a6268)}.btn-success{background:linear-gradient(135deg,var(--success),#20c997)}.btn-danger{background:linear-gradient(135deg,var(--danger),#c82333)}.status{padding:15px;border-radius:15px;margin:15px;text-align:center;font-weight:600;animation:slideIn .3s ease}@keyframes slideIn{from{opacity:0;transform:translateY(-20px)}to{opacity:1;transform:translateY(0)}}.success{background:rgba(40,167,69,.1);color:var(--success);border:2px solid var(--success)}.error{background:rgba(220,53,69,.1);color:var(--danger);border:2px solid var(--danger)}.modal{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.7);z-index:1000;justify-content:center;align-items:center;padding:20px}.modal.active{display:flex}.modal-content{background:var(--card);border-radius:25px;padding:30px;max-width:400px;width:100%;max-height:90vh;overflow-y:auto;animation:modalSlide .3s ease}@keyframes modalSlide{from{opacity:0;transform:scale(.9)}to{opacity:1;transform:scale(1)}}.modal-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}.modal-close{background:0 0;border:none;font-size:28px;cursor:pointer;color:var(--text);padding:0;width:auto}.qr-container{text-align:center;padding:20px}.qr-code{background:#fff;padding:20px;border-radius:15px;display:inline-block}.bottom-nav{position:fixed;bottom:0;left:0;right:0;max-width:480px;margin:0 auto;background:var(--card);border-top:1px solid var(--border);display:flex;justify-content:space-around;padding:10px 0;box-shadow:0 -5px 20px rgba(0,0,0,.05);z-index:100}.nav-item{text-align:center;padding:5px 15px;cursor:pointer;color:#888;text-decoration:none;transition:color .3s}.nav-item.active{color:var(--primary)}.nav-item .nav-icon{font-size:24px;margin-bottom:3px}.nav-item .nav-label{font-size:11px}.profile-header{text-align:center;padding:30px 20px;background:linear-gradient(135deg,var(--primary),var(--primary-light));color:#fff;border-radius:0 0 30px 30px}.profile-photo{width:100px;height:100px;border-radius:50%;background:#fff;margin:0 auto 15px;display:flex;align-items:center;justify-content:center;font-size:48px;box-shadow:0 10px 30px rgba(0,0,0,.2)}.profile-name{font-size:24px;font-weight:700;margin-bottom:5px}.profile-email{font-size:14px;opacity:.9}.menu-item{display:flex;align-items:center;padding:18px;margin:8px 0;background:var(--card);border-radius:15px;cursor:pointer;text-decoration:none;color:var(--text);transition:all .3s;border:1px solid var(--border)}.menu-item:hover{background:var(--bg);transform:translateX(5px)}.menu-item .menu-icon{font-size:24px;margin-right:15px;width:30px}.menu-item .menu-text{flex:1;font-weight:600}.menu-item .menu-arrow{color:#ccc}.page{display:none}.page.active{display:block;padding-bottom:80px}@media(max-width:480px){.actions{grid-template-columns:repeat(2,1fr)}.balance-amount{font-size:38px}}</style></head>
<body data-theme="{{session.get('theme','light')}}"><div class="app">
{% if session.get('user') %}
{% if session.get('admin') %}
<div class="page active"><div class="header"><div class="header-top"><h1>👨‍💼 Admin</h1><button class="theme-btn" onclick="toggleTheme()">🌙</button></div></div>
<div class="card"><div class="card-title">📊 Statistiques</div><div style="margin-top:20px"><p><strong>Utilisateurs:</strong> {{stats.total_users}}</p><p><strong>Agents:</strong> {{stats.total_agents}}</p><p><strong>Dépôts:</strong> {{"{:,.0f}".format(stats.total_deposits)}} FCFA</p><p><strong>Retraits:</strong> {{"{:,.0f}".format(stats.total_withdrawals)}} FCFA</p><p><strong>Balance:</strong> {{"{:,.0f}".format(platform_balance)}} FCFA</p></div></div>
<div class="card"><div class="card-title">📜 Transactions</div><div class="tx-list">{% for tx in all_transactions[:50] %}<div class="tx-item"><div class="tx-icon deposit">💸</div><div class="tx-details"><div class="tx-name">{{tx.user}} - {{tx.action}}</div><div class="tx-date">{{tx.timestamp[:19]}}</div></div><div class="tx-amount">{{"{:,.0f}".format(tx.amount)}} FCFA</div></div>{% endfor %}</div></div>
<button class="btn btn-danger" onclick="location.href='/logout'" style="margin:20px">🚪 Déconnexion</button></div>
{% else %}
<div class="page active" id="dashboard"><div class="header"><div class="header-top"><h1>💎 VoltCash</h1><button class="theme-btn" onclick="toggleTheme()">🌙</button></div><div class="balance"><div class="balance-label">Solde disponible</div><div class="balance-amount">{{"{:,.0f}".format(session.balance)}} FCFA</div></div></div>
<div class="actions"><a href="#" class="action-btn" onclick="showModal('sendModal')"><div class="icon">💸</div><div class="label">Envoyer</div></a><a href="#" class="action-btn" onclick="showModal('requestModal')"><div class="icon">📥</div><div class="label">Demander</div></a><a href="#" class="action-btn" onclick="showModal('qrModal')"><div class="icon">📱</div><div class="label">QR Code</div></a><a href="#" class="action-btn" onclick="showModal('depositModal')"><div class="icon">💰</div><div class="label">Ajouter</div></a><a href="#" class="action-btn" onclick="showModal('withdrawModal')"><div class="icon">🏦</div><div class="label">Retirer</div></a></div>
{% if success %}<div class="status success">✅ {{success|safe}}</div>{% endif %}{% if error %}<div class="status error">❌ {{error}}</div>{% endif %}
<div class="card"><div class="card-header"><div class="card-title">📊 Activité</div></div><div class="chart">{% for m in monthly_data %}<div><div class="chart-bar" style="height:{{(m.sent/10000)|int if m.sent>0 else 20}}px"></div><div class="chart-label">{{m.month}}</div></div>{% endfor %}</div></div>
<div class="card"><div class="card-header"><div class="card-title">📜 Transactions</div><a href="#" class="card-action" onclick="showPage('activity')">Voir tout</a></div><div class="tx-list">{% for tx in recent_transactions[:5] %}<div class="tx-item"><div class="tx-icon {{('received' if tx.action=='RECU' or tx.recipient==session.user else 'sent' if tx.action=='TRANSFER' else 'deposit')}}">{{('📥' if tx.action=='RECU' or tx.recipient==session.user else '📤' if tx.action=='TRANSFER' else '💰')}}</div><div class="tx-details"><div class="tx-name">{{tx.action}} {{tx.details[:30]}}</div><div class="tx-date">{{tx.timestamp[:10]}}</div></div><div class="tx-amount {{('positive' if tx.action in['RECU','DEPOT','INSCRIPTION']or(tx.recipient==session.user and tx.action=='TRANSFER')else'negative')}}">{{('+'if tx.action in['RECU','DEPOT','INSCRIPTION']or(tx.recipient==session.user and tx.action=='TRANSFER')else'-')}}{{"{:,.0f}".format(tx.amount)}} FCFA</div></div>{% endfor %}</div></div></div>
<div class="page" id="activity"><div class="header"><div class="header-top"><h1>📊 Activité</h1><button class="theme-btn" onclick="showPage('dashboard')">← Retour</button></div></div><div class="card"><input type="text" placeholder="🔍 Rechercher..." id="searchTx" onkeyup="filterTx()"></div><div class="card"><div class="tx-list">{% for tx in recent_transactions %}<div class="tx-item tx-searchable"><div class="tx-icon {{('received'if tx.action=='RECU'or tx.recipient==session.user else'sent'if tx.action=='TRANSFER'else'deposit')}}">{{('📥'if tx.action=='RECU'or tx.recipient==session.user else'📤'if tx.action=='TRANSFER'else'💰')}}</div><div class="tx-details"><div class="tx-name">{{tx.action}} - {{tx.details[:40]}}</div><div class="tx-date">{{tx.timestamp}} - {{tx.get('status','completed')}}</div></div><div class="tx-amount {{('positive'if tx.action in['RECU','DEPOT','INSCRIPTION']or(tx.recipient==session.user and tx.action=='TRANSFER')else'negative')}}">{{('+'if tx.action in['RECU','DEPOT','INSCRIPTION']or(tx.recipient==session.user and tx.action=='TRANSFER')else'-')}}{{"{:,.0f}".format(tx.amount)}} FCFA</div></div>{% endfor %}</div></div></div>
<div class="page" id="profile"><div class="profile-header"><div class="profile-photo">👤</div><div class="profile-name">{{session.name}}</div><div class="profile-email">{{session.user}}</div><p style="margin-top:10px;font-size:14px">Code: {{session.get('code','N/A')}}</p></div><div style="padding:20px"><a href="#" class="menu-item"><span class="menu-icon">👤</span><span class="menu-text">Profil</span><span class="menu-arrow">›</span></a><a href="#" class="menu-item"><span class="menu-icon">🔒</span><span class="menu-text">Sécurité</span><span class="menu-arrow">›</span></a><a href="#" class="menu-item"><span class="menu-icon">🔔</span><span class="menu-text">Notifications</span><span class="menu-arrow">›</span></a><a href="#" class="menu-item" onclick="toggleTheme()"><span class="menu-icon">🌙</span><span class="menu-text">Thème</span><span class="menu-arrow">›</span></a><a href="#" class="menu-item"><span class="menu-icon">❓</span><span class="menu-text">Aide</span><span class="menu-arrow">›</span></a></div><button class="btn btn-danger" onclick="location.href='/logout'" style="margin:20px">🚪 Déconnexion</button></div>
<div class="modal" id="sendModal"><div class="modal-content"><div class="modal-header"><h2>💸 Envoyer</h2><button class="modal-close" onclick="hideModal('sendModal')">×</button></div><form method="POST"><input type="email" name="recipient" placeholder="📧 Email destinataire" required><input type="number" name="amount" placeholder="💰 Montant" min="100" step="100" required><textarea name="note" placeholder="✍️ Note (optionnel)" rows="3"></textarea><input type="password" name="pin" placeholder="🔐 PIN" pattern="[0-9]{4}" required><button type="submit" name="action" value="transfer" class="btn">Envoyer GRATUITEMENT</button></form></div></div>
<div class="modal" id="requestModal"><div class="modal-content"><div class="modal-header"><h2>📥 Demander</h2><button class="modal-close" onclick="hideModal('requestModal')">×</button></div><form method="POST"><input type="email" name="from_user" placeholder="📧 De qui?" required><input type="number" name="amount" placeholder="💰 Montant" min="100" step="100" required><textarea name="reason" placeholder="📝 Raison" rows="3" required></textarea><button type="submit" name="action" value="request" class="btn btn-success">Créer demande</button></form></div></div>
<div class="modal" id="qrModal"><div class="modal-content"><div class="modal-header"><h2>📱 QR Code</h2><button class="modal-close" onclick="hideModal('qrModal')">×</button></div><div class="qr-container"><div class="qr-code"><img src="/qrcode?data={{session.user}}" alt="QR" style="max-width:250px"></div><p style="margin-top:20px">Scannez pour m'envoyer de l'argent</p><p style="margin-top:10px;font-size:14px;color:#888">{{session.user}}</p></div></div></div>
<div class="modal" id="depositModal"><div class="modal-content"><div class="modal-header"><h2>💰 Ajouter</h2><button class="modal-close" onclick="hideModal('depositModal')">×</button></div><form method="POST"><select name="method" required><option value="">Méthode</option><option value="mtn">📱 MTN Money</option><option value="orange">🍊 Orange Money</option><option value="card">💳 Carte</option><option value="bank">🏦 Virement</option></select><input type="number" name="amount" placeholder="💰 Montant" min="1000" step="100" required><p style="font-size:13px;color:#888;margin:10px 0">Frais: 2%</p><input type="password" name="pin" placeholder="🔐 PIN" pattern="[0-9]{4}" required><button type="submit" name="action" value="depot" class="btn btn-success">Déposer</button></form></div></div>
<div class="modal" id="withdrawModal"><div class="modal-content"><div class="modal-header"><h2>🏦 Retirer</h2><button class="modal-close" onclick="hideModal('withdrawModal')">×</button></div><form method="POST"><select name="method" required><option value="">Méthode</option><option value="mtn">📱 MTN Money</option><option value="orange">🍊 Orange Money</option><option value="bank">🏦 Virement</option></select><input type="number" name="amount" placeholder="💰 Montant" min="500" step="100" required><p style="font-size:13px;color:#888;margin:10px 0">Frais: 1%</p><input type="password" name="pin" placeholder="🔐 PIN" pattern="[0-9]{4}" required><button type="submit" name="action" value="retrait" class="btn btn-secondary">Retirer</button></form></div></div>
<div class="bottom-nav"><a href="#" class="nav-item active" onclick="showPage('dashboard')"><div class="nav-icon">🏠</div><div class="nav-label">Accueil</div></a><a href="#" class="nav-item" onclick="showPage('activity')"><div class="nav-icon">📊</div><div class="nav-label">Activité</div></a><a href="#" class="nav-item" onclick="showModal('sendModal')"><div class="nav-icon">💸</div><div class="nav-label">Envoyer</div></a><a href="#" class="nav-item" onclick="showPage('profile')"><div class="nav-icon">👤</div><div class="nav-label">Profil</div></a></div>
{% endif %}
{% else %}
<div class="header"><div class="header-top"><h1>💎 VoltCash Premium</h1><button class="theme-btn" onclick="toggleTheme()">🌙</button></div><p style="text-align:center;font-size:16px;opacity:.9;margin-top:10px">Transferts instantanés • Gratuits • Sécurisés</p></div>
{% if success %}<div class="status success">{{success|safe}}</div>{% endif %}{% if error %}<div class="status error">{{error}}</div>{% endif %}
<div class="card"><h2 style="margin-bottom:20px">🎉 Créer compte</h2><form method="POST"><input type="text" name="name" placeholder="👤 Nom" required><input type="email" name="email" placeholder="📧 Email" required><input type="tel" name="phone" placeholder="📱 Téléphone" required><input type="password" name="pin" placeholder="🔐 PIN 4 chiffres" pattern="[0-9]{4}" required><button type="submit" name="action" value="register" class="btn">S'inscrire - Bonus 5000 FCFA</button></form></div>
<div class="card"><h2 style="margin-bottom:20px">🚀 Connexion</h2><form method="POST"><input type="email" name="email" placeholder="📧 Email" required><input type="password" name="pin" placeholder="🔐 PIN" required><button type="submit" name="action" value="login" class="btn btn-secondary">Connexion</button></form></div>
<p style="text-align:center;margin:30px 20px;font-size:14px;color:#888">Admin: admin@voltcash.cm / 0000<br>Agent (1 Milliard): agent@voltcash.cm / 1234</p>
{% endif %}
</div>
<script>function showPage(p){document.querySelectorAll('.page').forEach(e=>e.classList.remove('active'));document.getElementById(p).classList.add('active');document.querySelectorAll('.nav-item').forEach(n=>n.classList.remove('active'))}function showModal(m){document.getElementById(m).classList.add('active')}function hideModal(m){document.getElementById(m).classList.remove('active')}function toggleTheme(){const b=document.body,c=b.getAttribute('data-theme'),n=c==='dark'?'light':'dark';b.setAttribute('data-theme',n);fetch('/theme',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({theme:n})})}function filterTx(){const i=document.getElementById('searchTx').value.toLowerCase();document.querySelectorAll('.tx-searchable').forEach(t=>{t.style.display=t.textContent.toLowerCase().includes(i)?'flex':'none'})}document.addEventListener('click',e=>{if(e.target.classList.contains('modal'))e.target.classList.remove('active')});if('serviceWorker'in navigator)navigator.serviceWorker.register('/sw.js')</script>
</body></html>'''

@app.route(’/manifest.json’)
def manifest():
return jsonify({“name”:“VoltCash Premium”,“short_name”:“VoltCash”,“start_url”:”/”,“display”:“standalone”,“background_color”:”#003087”,“theme_color”:”#003087”,“icons”:[{“src”:“https://via.placeholder.com/192x192/003087/FFF?text=VC”,“sizes”:“192x192”,“type”:“image/png”},{“src”:“https://via.placeholder.com/512x512/003087/FFF?text=VC”,“sizes”:“512x512”,“type”:“image/png”}]})

@app.route(’/sw.js’)
def service_worker():
return “const CACHE=‘v1’;self.addEventListener(‘install’,e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll([’/’]))));self.addEventListener(‘fetch’,e=>e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request))))”, 200, {‘Content-Type’:‘application/javascript’}

@app.route(’/qrcode’)
def generate_qr():
if not qrcode:
return “QR Code unavailable”, 404
data = request.args.get(‘data’, ‘voltcash.cm’)
qr = qrcode.QRCode(version=1, box_size=10, border=4)
qr.add_data(data)
qr.make(fit=True)
img = qr.make_image(fill_color=“black”, back_color=“white”)
buf = io.BytesIO()
img.save(buf, format=‘PNG’)
buf.seek(0)
return send_file(buf, mimetype=‘image/png’)

@app.route(’/theme’, methods=[‘POST’])
def set_theme():
data = request.get_json()
session[‘theme’] = data.get(‘theme’, ‘light’)
if session.get(‘user’) and session[‘user’] in users:
users[session[‘user’]][‘theme’] = session[‘theme’]
save_data()
return jsonify({‘success’: True})

@app.route(’/’, methods=[‘GET’, ‘POST’])
def index():
error = success = None
monthly_data = []
recent_transactions = []
all_transactions = []

```
if request.method == 'POST':
    action = request.form.get('action')
    email = request.form.get('email', '').lower().strip()
    pin = request.form.get('pin', '').strip()
    
    if action == 'register':
        if email in users:
            error = "Compte existant"
        elif len(pin) != 4 or not pin.isdigit():
            error = "PIN = 4 chiffres"
        else:
            code = generate_code()
            users[email] = {
                'name': request.form.get('name', email),
                'phone': request.form.get('phone', ''),
                'pin': hash_pin(pin),
                'balance': Decimal('5000'),
                'code': code,
                'created': datetime.now().isoformat(),
                'type': 'user',
                'theme': 'light'
            }
            log_tx(email, 'INSCRIPTION', 5000, f'Bonus - Code: {code}')
            stats['total_users'] = stats.get('total_users', 0) + 1
            save_data()
            session['user'] = email
            session['name'] = users[email]['name']
            session['balance'] = float(users[email]['balance'])
            session['theme'] = 'light'
            session['code'] = code
            success = f'Bienvenue! Compte cree avec <strong>5000 FCFA</strong>!<br>Code: <strong>{code}</strong>'
    
    elif action == 'login':
        if email == ADMIN_EMAIL and pin == ADMIN_PIN:
            session['user'] = email
            session['admin'] = True
            session['name'] = 'Admin'
            session['balance'] = 0
            success = "Admin connecte"
        elif email in users and users[email]['pin'] == hash_pin(pin):
            session['user'] = email
            session['name'] = users[email]['name']
            session['balance'] = float(users[email]['balance'])
            session['theme'] = users[email].get('theme', 'light')
            session['code'] = users[email].get('code', '')
            success = "Connexion reussie!"
        else:
            error = "Email ou PIN incorrect"
    
    elif action == 'transfer' and 'user' in session:
        sender = session['user']
        recipient = request.form.get('recipient', '').lower().strip()
        note = request.form.get('note', '')
        try:
            amount = Decimal(request.form.get('amount', '0'))
            if recipient not in users:
                error = "Destinataire introuvable"
            elif sender == recipient:
                error = "Pas a soi-meme"
            elif users[sender]['balance'] < amount:
                error = f"Solde insuffisant"
            elif users[sender]['pin'] != hash_pin(pin):
                error = "PIN incorrect"
            else:
                users[sender]['balance'] -= amount
                users[recipient]['balance'] += amount
                session['balance'] = float(users[sender]['balance'])
                log_tx(sender, 'TRANSFER', amount, note or f'Vers {users[recipient]["name"]}', 0, recipient)
                log_tx(recipient, 'RECU', amount, note or f'De {users[sender]["name"]}', 0, sender)
                success = f'{int(amount):,} FCFA transferes!'
                save_data()
        except:
            error = "Montant invalide"
    
    elif action == 'depot' and 'user' in session:
        try:
            amount = Decimal(request.form.get('amount', '0'))
            method = request.form.get('method', '')
            sender = session['user']
            if users[sender]['pin'] != hash_pin(pin):
                error = "PIN incorrect"
            elif amount < 1000:
                error = "Min: 1000 FCFA"
            else:
                fee = amount * COMMISSIONS['depot']
                net = amount - fee
                users[sender]['balance'] += net
                global platform_balance
                platform_balance += fee
                session['balance'] = float(users[sender]['balance'])
                log_tx(sender, 'DEPOT', amount, f'{method} - Net: {int(net)}', fee)
                stats['total_deposits'] = stats.get('total_deposits', 0) + float(amount)
                success = f'{int(amount):,} FCFA deposes! Net: {int(net):,} (Frais: {int(fee):,})'
                save_data()
        except:
            error = "Depot echoue"
    
    elif action == 'retrait' and 'user' in session:
        try:
            amount = Decimal(request.form.get('amount', '0'))
            method = request.form.get('method', '')
            sender = session['user']
            if users[sender]['pin'] != hash_pin(pin):
                error = "PIN incorrect"
            elif amount < 500:
                error = "Min: 500 FCFA"
            else:
                fee = amount * COMMISSIONS['retrait']
                total = amount + fee
                if users[sender]['balance'] >= total:
                    users[sender]['balance'] -= total
                    platform_balance += fee
                    session['balance'] = float(users[sender]['balance'])
                    log_tx(sender, 'RETRAIT', amount, f'{method} - Total: {int(total)}', fee)
                    stats['total_withdrawals'] = stats.get('total_withdrawals', 0) + float(amount)
                    success = f'{int(amount):,} FCFA retires! (Frais: {int(fee):,})'
                    save_data()
                else:
                    error = f"Solde insuffisant"
        except:
            error = "Retrait echoue"
    
    elif action == 'request' and 'user' in session:
        from_user = request.form.get('from_user', '').lower().strip()
        amount = request.form.get('amount', '0')
        reason = request.form.get('reason', '')
        if from_user in users:
            payment_requests.append({
                'id': 'REQ' + secrets.token_hex(6).upper(),
                'from': from_user,
                'to': session['user'],
                'amount': amount,
                'reason': reason,
                'status': 'pending',
                'created': datetime.now().isoformat()
            })
            save_data()
            success = "Demande envoyee!"
        else:
            error = "Utilisateur introuvable"

if session.get('user'):
    if session.get('admin'):
        all_transactions = transactions[:100]
    else:
        recent_transactions = get_user_transactions(session['user'], 100)
        monthly_data = get_monthly_stats(session['user'])

return render_template_string(HTML_TEMPLATE, 
                             session=session, 
                             success=success, 
                             error=error,
                             recent_transactions=recent_transactions,
                             all_transactions=all_transactions,
                             monthly_data=monthly_data,
                             platform_balance=float(platform_balance),
                             stats=stats)
```

@app.route(’/logout’)
def logout():
session.clear()
return redirect(’/’)

if **name** == ‘**main**’:
port = int(os.environ.get(‘PORT’, 5000))
app.run(host=‘0.0.0.0’, port=port, debug=False)
