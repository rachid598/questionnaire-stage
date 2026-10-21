import os, csv, io, sqlite3, secrets
from datetime import datetime, timezone
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, Response, abort

app=Flask(__name__)
app.secret_key=os.environ.get('SECRET_KEY') or secrets.token_hex(32)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax', MAX_CONTENT_LENGTH=16384)
DB=os.environ.get('DB_PATH','/data/responses.sqlite3')
ADMIN_PASSWORD=os.environ.get('ADMIN_PASSWORD','')
# Horaires UTC ISO 8601 avec fuseau, optionnels : 2026-10-22T08:00:00+02:00
def configured_time(name):
    value=os.environ.get(name,'').strip()
    if not value: return None
    parsed=datetime.fromisoformat(value)
    if parsed.tzinfo is None: raise ValueError(f'{name} doit contenir un fuseau horaire')
    return parsed.astimezone(timezone.utc)
OPENS_AT=configured_time('OPENS_AT')
CLOSES_AT=configured_time('CLOSES_AT')
if OPENS_AT and CLOSES_AT and OPENS_AT >= CLOSES_AT: raise ValueError('CLOSES_AT doit être après OPENS_AT')
def is_open():
    now=datetime.now(timezone.utc)
    return (not OPENS_AT or now >= OPENS_AT) and (not CLOSES_AT or now < CLOSES_AT)

FIELDS=['inscription_parents','inscription_soi','inscription_professeurs','presence','absence_raison','ambiance','activites','progres','renouveler','revenir','modifier','expliquer']
YESNO={'Oui','Non'}
REASONS={'Rendez-vous médical','Pas motivé(e)','Raison personnelle'}
FEELINGS={'À l’aise, l’ambiance était agréable','Pas à l’aise, j’avais du mal avec le groupe'}

def connect():
    os.makedirs(os.path.dirname(os.path.abspath(DB)),exist_ok=True)
    con=sqlite3.connect(DB,timeout=15)
    con.row_factory=sqlite3.Row
    con.execute('PRAGMA busy_timeout=15000')
    con.execute('PRAGMA journal_mode=WAL')
    return con

def initialize():
    with connect() as con:
        con.execute('CREATE TABLE IF NOT EXISTS submissions (id INTEGER PRIMARY KEY AUTOINCREMENT, submitted_at TEXT NOT NULL, '+', '.join(f'{f} TEXT' for f in FIELDS)+')')
initialize()

def validate(d):
    errors=[]
    for f in ('inscription_parents','inscription_soi','inscription_professeurs','presence','activites','progres','renouveler','revenir','modifier'):
        if d.get(f) not in YESNO: errors.append(f)
    if d.get('ambiance') not in FEELINGS: errors.append('ambiance')
    if d.get('presence')=='Non' and d.get('absence_raison') not in REASONS: errors.append('absence_raison')
    if d.get('modifier')=='Oui' and not d.get('expliquer','').strip(): errors.append('expliquer')
    if len(d.get('expliquer',''))>1500: errors.append('expliquer')
    return errors

@app.get('/')
def form():
    if not is_open(): return ('Ce questionnaire est fermé pour le moment.', 503)
    session.setdefault('csrf_token', secrets.token_urlsafe(32))
    return render_template('form.html',done=False,csrf_token=session['csrf_token'])

@app.post('/submit')
def submit():
    if not is_open(): return ('Ce questionnaire est fermé. Les réponses ne sont plus acceptées.', 403)
    if not session.get('csrf_token') or not secrets.compare_digest(request.form.get('csrf_token',''),session['csrf_token']): abort(403)
    d={f:request.form.get(f,'').strip() for f in FIELDS}
    if d['presence']!='Non': d['absence_raison']=''
    if d['modifier']!='Oui': d['expliquer']=''
    problems=validate(d)
    if problems: return render_template('form.html',done=False,error='Certaines réponses obligatoires manquent ou sont incorrectes. Vérifie le questionnaire.',values=d,csrf_token=session['csrf_token']),400
    with connect() as con:
        con.execute('INSERT INTO submissions (submitted_at,'+','.join(FIELDS)+') VALUES ('+','.join(['?']*(1+len(FIELDS)))+')',[datetime.now(timezone.utc).isoformat(timespec='seconds')]+[d[f] for f in FIELDS])
    session.pop('csrf_token',None)
    return render_template('form.html',done=True)

def require_admin(fn):
    @wraps(fn)
    def wrapper(*args,**kwargs):
        if not session.get('admin'): return redirect(url_for('login'))
        return fn(*args,**kwargs)
    return wrapper

@app.route('/admin/login',methods=['GET','POST'])
def login():
    if not ADMIN_PASSWORD: return 'Définissez ADMIN_PASSWORD sur le serveur pour activer le tableau enseignant.',503
    if request.method=='POST':
        supplied=request.form.get('password','')
        if secrets.compare_digest(supplied,ADMIN_PASSWORD):
            session.clear();session['admin']=True;return redirect(url_for('admin'))
        flash('Mot de passe incorrect.')
    return render_template('login.html')

@app.post('/admin/logout')
@require_admin
def logout():
    session.clear();return redirect(url_for('form'))

@app.get('/admin')
@require_admin
def admin():
    with connect() as con:
        count=con.execute('SELECT COUNT(*) FROM submissions').fetchone()[0]
        recent=con.execute('SELECT id,submitted_at,presence,ambiance,activites,progres,renouveler,revenir FROM submissions ORDER BY id DESC LIMIT 30').fetchall()
    return render_template('admin.html',count=count,recent=recent)

@app.get('/admin/export.csv')
@require_admin
def export():
    output=io.StringIO(); writer=csv.writer(output,delimiter=';')
    writer.writerow(['id','date_utc']+FIELDS)
    with connect() as con:
        for row in con.execute('SELECT id, submitted_at,'+','.join(FIELDS)+' FROM submissions ORDER BY id'):
            # Éviter l'interprétation de formules CSV dans Excel/Calc.
            vals=[("'"+v if isinstance(v,str) and v[:1] in ('=','+','-','@') else v) for v in row]
            writer.writerow(vals)
    csv_data='\ufeff'+output.getvalue()
    return Response(csv_data,mimetype='text/csv; charset=utf-8',headers={'Content-Disposition':'attachment; filename="reponses-stage.csv"','Cache-Control':'no-store'})

@app.after_request
def headers(response):
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['X-Frame-Options']='DENY'
    response.headers['Referrer-Policy']='no-referrer'
    response.headers['Cache-Control']='no-store'
    return response

if __name__=='__main__':
    app.run(debug=False,host='127.0.0.1',port=8000)
