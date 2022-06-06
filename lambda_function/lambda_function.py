import json
from datetime import date
import datetime
import pymysql
import smtplib
from email.message import EmailMessage

today = date.today()

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

'''
sql = "SELECT machine_id,email,maintain_date FROM maintain_schedule WHERE maintain_date=(%s)"
cur.execute(sql, (today+datetime.timedelta(days=1)))
conn.commit()
rows = cur.fetchall()
sql = "SELECT machine_id,email,next_maintain FROM maintain_schedule WHERE next_maintain=(%s)"
cur.execute(sql, (today+datetime.timedelta(days=1)))
conn.commit()
rows = rows + cur.fetchall()
'''

send_sql = "SELECT M.machine_id, Mem.email, M.start_date FROM Maintenance M, `Member` Mem WHERE M.start_date =(%s) AND M.member_id = Mem.account"
cur.execute(send_sql, (today+datetime.timedelta(days=1)))
conn.commit()
rows = cur.fetchall()
send_sql = "SELECT M.machine_id, Mem.email, M.next_maintain_date FROM Maintenance M, `Member` Mem WHERE M.next_maintain_date =(%s) AND M.member_id = Mem.account"
cur.execute(send_sql, (today+datetime.timedelta(days=1)))
conn.commit()
rows = rows + cur.fetchall()

d = {}
for r in rows:
	d[r[0]] = [r[1],r[2]] # machine_id = [email, next_maintain_date]
	
k = list(d.keys())


# 更新維修日期
'''
sql="UPDATE maintain_schedule "\
    "SET "\
    "maintain_date = next_maintain, "\
    "next_maintain = DATE_ADD(next_maintain , INTERVAL day_diff DAY) "\
    "WHERE machine_id = machine_id AND maintain_date<(%s)"

cur.execute(sql, today)
conn.commit()
'''

check_sql = "SELECT machine_id FROM Maintenance WHERE next_maintain_date <= (%s) "
cur.execute(check_sql, (today))
conn.commit()
check_rows = cur.fetchall()

if len(check_rows) > 0:

    update_sql="UPDATE Maintenance "\
    "SET "\
    "last_maintain_date = next_maintain_date, "\
    "next_maintain_date = DATE_ADD(next_maintain_date , INTERVAL maintain_freq DAY) "\
    "WHERE machine_id = machine_id AND maintain_date <=(%s)"
    cur.execute(update_sql, (today))
    conn.commit()

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
    msg.set_content('維護機台ID為： ' + machine_id + ' on '+ str(d[machine_id][1]))
    
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