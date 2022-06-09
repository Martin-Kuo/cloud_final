import json
from datetime import date
import datetime
import pymysql
import smtplib
from email.message import EmailMessage

# today = date.today()
today = datetime.datetime.now()
today = today+datetime.timedelta(hours=8)
tomorrow = today+datetime.timedelta(days=1)
tomorrow = datetime.datetime.strftime(tomorrow, "%Y-%m-%d")
today = datetime.datetime.strftime(today, "%Y-%m-%d")

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

cur=conn.cursor()

# 找出當日維修的機器
check_sql = "SELECT machine_id FROM Maintenance WHERE next_maintain_date = (%s) "
cur.execute(check_sql, (today))
conn.commit()
check_rows = cur.fetchall()

if len(check_rows) > 0:

    update_sql="UPDATE Maintenance "\
    "SET "\
    "last_maintain_date = next_maintain_date, "\
    "next_maintain_date = DATE_ADD(next_maintain_date , INTERVAL maintain_freq DAY) "\
    "WHERE machine_id = machine_id AND next_maintain_date =(%s)"
    cur.execute(update_sql, (today))
    conn.commit()

# 找出隔天需要維護的機器(next_maintain_date)
send_sql = "SELECT M.machine_id, Mem.email, M.next_maintain_date FROM Maintenance M, `Member` Mem WHERE M.next_maintain_date =(%s) AND M.member_id = Mem.account"
cur.execute(send_sql, (tomorrow))
conn.commit()
rows = cur.fetchall()

d = {}
for r in rows:
	d[r[0]] = [r[1],r[2]] # machine_id = [email, next_maintain_date]
	
k = list(d.keys())

def lambda_handler(event, context):
    
    if k:
        for machine_id in k:
            send_email(machine_id)
    
    return {
        'statusCode': 200,
        'body': json.dumps('Successfully sent email from Lambda using Amazon SES')
    }
   
def send_email(machine_id):
    gmail_user = 'zexon02@gmail.com'
    gmail_app_password = 'ehxlvsituvqehkfl'
    
    msg = EmailMessage()
    msg['Subject'] = '機器維護通知'
    msg['From'] = gmail_user
    msg['To'] = d[machine_id][0]
    msg.set_content('您有機台： ' + machine_id + ' 需於 '+ str(d[machine_id][1])) + ' 維護。 '
    
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(gmail_user, gmail_app_password)
        #server.sendmail(sent_from, sent_to, email_text)
        server.send_message(msg)
        server.close()
        print('Email sent!')
    except Exception as exception:
        print("Error: %s!\n\n" % exception)