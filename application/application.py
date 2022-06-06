from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import date
import datetime
import pymysql
import os
import smtplib
from email.message import EmailMessage

# 本地測試資料庫
'''
conn = pymysql.connect(
        host= 'localhost', 
        port = 3306,
        user = 'root', 
        password = 'root',
        db = 'machine',
    )
'''

# 連上資料庫(Jason的)
'''
conn = pymysql.connect(
        host= 'machinedatabase.cy453mcnxqjo.us-east-1.rds.amazonaws.com', 
        port = 3306,
        user = 'admin', 
        password = 'rootroot',
        db = 'sys'
    )
'''
# 連上資料庫(Cindy的)
conn = pymysql.connect(
        host= 'mydb.cmqgfis3u1l2.us-east-1.rds.amazonaws.com', 
        port = 3306,
        user = 'admin', 
        password = '01234567',
        db = 'sys'
    )

cur=conn.cursor() # 類似指標

application = Flask(__name__) # 定位目前載入資料夾的位置, WSGIPath:要設application
application.config['SECRET_KEY'] = os.urandom(24) # 加密用金鑰

data = {}

# 登入頁面
@application.route('/')
def start():
    return render_template('login.html')

# 登入
@application.route('/login', methods=['POST', 'GET'])
def login():
    account = request.form.get('account')
    password = request.form.get('password')
    target = None
    login_sql = "SELECT account,username,password,admin FROM `Member` WHERE account=(%s)"
    cur.execute(login_sql,(account))
    conn.commit()
    target = cur.fetchone()
    
    if target == None:
        flash("您尚未註冊!") 
        return render_template('login.html')
    elif password != target[2]:
        flash("輸入密碼錯誤!") 
        return render_template('login.html')
    else:
        session['account'] = target[0] # 記錄使用者登入session
        session['username'] = target[1]
        session['flag'] = target[3]
        return redirect(url_for('index'))
        
        

# 主頁面
@application.route('/index')
def index():
    if 'account' in session: # 如果使用者是登入狀態
        username = session['username']
        account = session['account']
        flag = session['flag']
        search_flag = 0

        if flag == 'Y':
            sql = "SELECT M.* , Mem.`username` FROM `Maintenance` M LEFT JOIN `Member` Mem ON M.member_id = Mem.`account` ORDER BY next_maintain_date"
            cur.execute(sql)
            conn.commit()
            rows = cur.fetchall()

        else:
            sql = "SELECT M.* , Mem.`username` FROM ( SELECT * FROM `Maintenance` WHERE member_id = (%s)) M LEFT JOIN `Member` Mem ON M.member_id = Mem.`account` ORDER BY next_maintain_date"
            cur.execute(sql,(account))
            conn.commit()
            rows = cur.fetchall()

        data = {}
        for r in rows:
            data[r[0]] = [r[8],r[2],r[3],r[4],r[5],r[6],r[7]] # machine_id = username, start_date, end_date, last_maintain_date, next_maintain_date, state, maintain_freq, 
        return render_template('index.html', username = username, account = account, data=data, search_flag=search_flag)

# 註冊頁面
@application.route('/signup')
def signup():
    return render_template('signup.html')

# 註冊
@application.route('/signup_act', methods=['POST', 'GET'])
def signup_act():
    username = request.form.get('username')
    account = request.form.get('account')
    password = request.form.get('password')
    email = request.form.get('email')
    target = None
    repeat_sql = "SELECT account FROM `Member` WHERE account=(%s)"
    cur.execute(repeat_sql,(account))
    conn.commit()
    target = cur.fetchone()

    if target == None:
        signup_sql = "INSERT INTO `Member` (`username`, `account`, `password`, `email`) VALUES (%s, %s, %s, %s)"
        cur.execute(signup_sql,(username, account, password, email))
        conn.commit()
        return render_template('login.html')
    else:
        flash("此帳號已被註冊!") 
        return render_template('signup.html')

# 登出
@application.route('/logout')
def logout():
    session.pop('account', None)
    session.pop('username', None)    
    return redirect(url_for('start'))

# 新增頁面
@application.route('/add')
def add():
    username = session['username']
    account = session['account']
    flag = session['flag']
    list ={}

    if flag == 'Y':
        sql = "SELECT account,username FROM `Member`"
        cur.execute(sql)
        conn.commit()
        rows = cur.fetchall()
        for i in rows:
            list[i[0]] = [i[0],i[1]]

    return render_template('add.html', username = username, account = account, flag = flag, list =list)

# 新增
@application.route('/insert', methods=['POST', 'GET'])
def insert():
    username = session['username']
    account = session['account']
    flag = session['flag']

    # 找出郵件
    email_sql = "SELECT email FROM `Member` WHERE account=(%s)"
    cur.execute(email_sql,(account))
    conn.commit()
    email = cur.fetchone()

    # 新增維護機器
    acc = request.form.get('account')
    machine_id = request.form.get('machine_id')
    same = None

    sql = "SELECT * FROM `Maintenance` WHERE machine_id=(%s)"
    cur.execute(sql,(machine_id))
    conn.commit()
    same = cur.fetchone()
    if same != None: # 如果machine id重複，提醒
        flash("機器已存在!") 
        return render_template('add.html', username = username, account = account)
    start_date = request.form.get('start_date')
    maintain_freq = request.form.get('maintain_freq')
    today = str(date.today())
    # next_maintain_date = datetime.datetime.strptime(start_date, "%Y-%m-%d") + datetime.timedelta(days=int(maintain_freq))
    insert_sql = "INSERT INTO `Maintenance` (`machine_id`, `member_id`, `start_date`, `next_maintain_date`, `maintain_freq`) VALUES (%s, %s, %s, %s, %s)"

    if flag == 'Y':
        cur.execute(insert_sql,(machine_id, acc, today, start_date.date(), maintain_freq))
    else:
        cur.execute(insert_sql,(machine_id, account, today, start_date.date(), maintain_freq))

    conn.commit()

    return redirect(url_for('index'))
    
'''
 # 如果是明天要維修,寄郵件通知
    today = str(date.today())
    check = datetime.datetime.strptime(today, "%Y-%m-%d")+datetime.timedelta(days=1)

    if (str(check.date())) == str(next_maintain_date.date()):
        send_email(email, machine_id, next_maintain_date.date())
    
'''

# 查詢
@application.route('/searching', methods=['POST', 'GET'])
def searching():
    username = session['username']
    account = session['account']
    flag = session['flag']
    machine_id = request.args.get('machine_id')
    search_flag =1

    if flag == 'Y':
        searching_sql = "SELECT M.* , Mem.`username` FROM ( SELECT * FROM `Maintenance` WHERE machine_id = (%s)) M LEFT JOIN `Member` Mem ON M.member_id = Mem.`account`"
        cur.execute(searching_sql,(machine_id))
        conn.commit()
        rows = cur.fetchall()
    else:
        searching_sql = "SELECT M.* , Mem.`username` FROM ( SELECT * FROM `Maintenance` WHERE machine_id = (%s) AND member_id = (%s)) M LEFT JOIN `Member` Mem ON M.member_id = Mem.`account`"
        cur.execute(searching_sql,(machine_id,account))
        conn.commit()
        rows = cur.fetchall()

    data = {}
    if len(rows) == 0:
        flash("找不到機器!") 
        return render_template('index.html', username = username, account = account, data=data, search_flag=search_flag)
    else:
        for r in rows:
            data[r[0]] = [r[8],r[2],r[3],r[4],r[5],r[6],r[7]] # machine_id = username, start_date, end_date, last_maintain_date, next_maintain_date, state, maintain_freq, 
        return render_template('index.html', username = username, account = account, search=data, data = data, search_flag=search_flag)

# 刪除
@application.route('/remove', methods=['POST'])
def remove():
    if request.method == 'POST':
        machine_id = request.form.get('machine_id')
        sql = "DELETE FROM `Maintenance` WHERE machine_id=(%s)"
        cur.execute(sql,(machine_id))
        conn.commit()
        return redirect(url_for('index'))

# 寄郵件
'''
def send_email(user, machine_id, date):
    gmail_user = 'zexon02@gmail.com'
    gmail_app_password = 'ehxlvsituvqehkfl'
    
    msg = EmailMessage()
    msg['Subject'] = 'Machine Notification'
    msg['From'] = gmail_user
    msg['To'] = user
    msg.set_content('Please maintain your machine ' + machine_id + ' on '+ str(date))
    
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465) # 設定SMTP伺服器
        server.ehlo() # 驗證SMTP伺服器
        server.login(gmail_user, gmail_app_password)
        server.send_message(msg)
        server.close()
        print('Email sent!')
    except Exception as exception:
        print("Error: %s!\n\n" % exception)
'''


if __name__ == '__main__':
    application.run(debug = True)
