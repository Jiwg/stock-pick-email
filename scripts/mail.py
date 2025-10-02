import os,yagmail,json,pandas as pd
pick = pd.read_csv('pick.csv')
new  = json.loads(os.getenv('NEW_SIGNALS'))
gone = json.loads(os.getenv('GONE_SIGNALS'))

subject = f"🔥严格策略+温度图 {len(pick)} 只潜力龙头 {pd.Timestamp.today().strftime('%Y-%m-%d')}"
body = "<html><body><h3>沪深300估值温度</h3><img src='cid:temp_bar'><hr><h3>本周标的</h3>"
for _,r in pick.iterrows():
    body+=f"<p><b>{r['name']}</b>（{r['ts_code']}）<br>关键指标：PB={r['pb']:.2f}  ROE={r['roe']:.1f}%  量比={r['vol_ratio']:.1f}<br><img src='cid:{r['ts_code']}' width='400'></p>"

if new:
    body+=f"<hr><h4>🆕 新增信号 {len(new)} 只："+','.join([c['name'] for c in new])+ "</h4>"
if gone:
    body+=f"<hr><h4>❌ 剔除信号 {len(gone)} 只："+','.join([c['name'] for c in gone])+ "</h4>"
body+="</body></html>"

yagmail.register(os.getenv('MAIL_USER'),os.getenv('MAIL_PASS'))
yag = yagmail.SMTP(os.getenv('MAIL_USER'),host='smtp.163.com',port=465)
attachments=[os.getenv('TEMP_PIC')]+os.getenv('KLINE_PICS').split(',')
yag.send(to=os.getenv('MAIL_TO'),subject=subject,contents=body,attachments=attachments)
print('带图+增删提醒邮件已发送')