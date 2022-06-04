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

# 連上資料庫
conn = pymysql.connect(
        host= 'machinedatabase.cy453mcnxqjo.us-east-1.rds.amazonaws.com', 
        port = 3306,
        user = 'admin', 
        password = 'rootroot',
        db = 'sys'
        )

cur=conn.cursor() # 類似指標

application = Flask(__name__) # 定位目前載入資料夾的位置, WSGIPath:要設application
application.config['SECRET_KEY'] = os.urandom(24) # 加密用金鑰

data = {}

# 主頁
@application.route('/')
def index():
    if 'username' in session: # 如果使用者是登入狀態
        user = session['username']
        sql = "SELECT * FROM maintain_schedule"
        cur.execute(sql)
        conn.commit()
        rows = cur.fetchall()
        for r in rows:
            data[r[0]] = [r[1],r[2],r[3],r[4]] # machine_id = maintain_date, day_diff, next_maintain, email
        return render_template('index.html', session = user, data=data)
    else:
        return render_template('login.html')

#註冊
@application.route('/signup')
def signup():
    return render_template('signup.html')

# 登入
@application.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        usr = request.form.get('username')
        session['username'] = usr # 記錄使用者登入session
        return redirect(url_for('index'))
    else:
        return render_template('login.html')

# 登出
@application.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

#新增頁面
@application.route('/add')
def add():
    return render_template('add.html')

# 新增
@application.route('/submit', methods=['POST', 'GET'])
def submit():
    user = session['username']
    if request.method == 'POST':
        machine_id = request.form.get('machine_id')
        if machine_id in data: # 如果machine id重複，提醒
            flash("Machine exists!") 
            return render_template('index.html', session = user, data=data)
        maintain_date = request.form.get('maintain_date')
        interval = request.form.get('interval')
        next_maintain_date = datetime.datetime.strptime(maintain_date, "%Y-%m-%d") + datetime.timedelta(days=int(interval))
        sql = "INSERT INTO `maintain_schedule` (`machine_id`, `maintain_date`, `day_diff`, `next_maintain`, `email`) VALUES (%s, %s, %s, %s, %s)"
        cur.execute(sql,(machine_id, maintain_date, interval, next_maintain_date.date(), user))
        conn.commit()
        # 如果是明天要維修,寄郵件通知
        today = str(date.today())
        check = datetime.datetime.strptime(today, "%Y-%m-%d")+datetime.timedelta(days=1)
        if (str(check.date())) == maintain_date:
            send_email(user, machine_id, maintain_date)
        if (str(check.date())) == str(next_maintain_date.date()):
            send_email(user, machine_id, next_maintain_date.date())
        return redirect(url_for('index'))
    else:
        target = None
        machine_id = request.args.get('machine_id')
        sql = "SELECT * FROM `maintain_schedule` WHERE machine_id=(%s)"
        cur.execute(sql,(machine_id))
        conn.commit()
        target = cur.fetchone()
        if target == None:
            flash("Machine not found!") 
            return render_template('index.html', session = user, data=data)
        return render_template('index.html', session = user, search=target, data=data)

# 刪除
@application.route('/remove', methods=['POST'])
def remove():
    if request.method == 'POST':
        machine_id = request.form.get('machine_id')
        sql = "DELETE FROM `maintain_schedule` WHERE machine_id=(%s)"
        cur.execute(sql,(machine_id))
        conn.commit()
        del data[machine_id]
        return redirect(url_for('index'))

# 寄郵件
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

if __name__ == '__main__':
    application.run(debug = True)
