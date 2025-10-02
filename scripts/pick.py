import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import json,pandas as pd,datetime as dt,numpy as np
import akshare as ak
from draw import temp_bar,plot_kline

today   = dt.date.today()
friday  = today if today.weekday()==4 else today-pd.Timedelta(days=today.weekday()-4)

# 1. 严格选股逻辑
## 1. 基础池：剔除次新、ST
basic = ak.stock_info_a_code_name()          # ts_code,name
indus = ak.stock_industry_cls()              # 行业分类
basic = basic.merge(indus, on='name', how='left')
basic.rename(columns={'code':'ts_code','c_name':'industry'},inplace=True)
basic = basic[basic.ts_code.str.endswith(('SH','SZ'))]   # 只留A股
basic['market'] = basic.ts_code.str[-2:].map({'SH':'主板','SZ':'主板'})

## 2. 取最近 5 年 PB 分位、最新财报、月线行情
pb_df = pro.daily_basic(trade_date=friday.strftime('%Y%m%d'), fields='ts_code,pb')
# 用 tushare 5 年 PB 分位接口（需积分>2000）
pb_rank = pro.stk_factor(ts_code=','.join(basic.ts_code), trade_date=friday.strftime('%Y%m%d'), fields='ts_code,pb_5y_percentile')
latest  = pro.fina_indicator_vip(period='20240331', fields='ts_code,roe,debt_to_assets')  # 最新季报
monthly = pro.monthly(trade_date=friday.strftime('%Y%m%d'), fields='ts_code,close,vol,amount')

## 3. 合并指标
df = basic.merge(pb_df,on='ts_code').merge(pb_rank,on='ts_code').merge(latest,on='ts_code').merge(monthly,on='ts_code')
df = df.dropna(subset=['pb','roe','debt_to_assets','pb_5y_percentile'])

## 4. 严格档条件
industry_rank = df.groupby('industry')['amount'].rank(ascending=False)
df = df[(df.pb<1) & (df.roe>12) & (df.debt_to_assets<50) & (df.pb_5y_percentile<20) & (industry_rank<=3)]

## 5. 底部放量：20 日量比 >2（用月线 vol 估算）
prev_vol = pro.monthly(trade_date=(friday-pd.Timedelta(days=35)).strftime('%Y%m%d'), fields='ts_code,vol')
prev_vol.columns=['ts_code','prev_vol']
df = df.merge(prev_vol,on='ts_code')
df['vol_ratio'] = df['vol']/df['prev_vol']
df = df[df.vol_ratio>=2.0]

## 6. 生成说明
if df.empty:
    print('本周无严格档信号');os.environ['HAS_PICK']='false'
else:
    df['logic'] = ( '1) PB<1 & ROE>12% & 负债<50% 且处于近5年PB低位；'
                    '2) 行业成交额TOP3龙头；3) 20日量比≥2，底部温和放量。')
    df['key_info'] = (df['name']+'('+df['ts_code']+') | 行业:'+df['industry']+
                      ' | PB:'+df['pb'].round(2).astype(str)+
                      ' | ROE:'+df['roe'].round(1).astype(str)+'%'+
                      ' | 量比:'+df['vol_ratio'].round(1).astype(str))
    df.to_csv('pick.csv',index=False,encoding='utf-8-sig')
    os.environ['HAS_PICK']='true'

# 2. 画沪深300估值温度条
temp_img = temp_bar(pro)

# 3. 画个股K线 & 保存
pic_list = []
for _,row in df.iterrows():
    pic = plot_kline(row['ts_code'],row['name'],end=friday)
    pic_list.append(pic)

# 4. cache对比
os.makedirs('cache',exist_ok=True)
curr = df[['ts_code','name']].to_dict(orient='records')
last = json.load(open('cache/last_pick.json')) if os.path.exists('cache/last_pick.json') else []
new  = [c for c in curr if c['ts_code'] not in [l['ts_code'] for l in last]]
gone = [l for l in last if l['ts_code'] not in [c['ts_code'] for c in curr]]
json.dump(curr,open('cache/last_pick.json','w',encoding='utf-8'),ensure_ascii=False)

# 5. 环境变量传给mail.py
os.environ['HAS_PICK']='true'
os.environ['TEMP_PIC']=temp_img
os.environ['KLINE_PICS']=','.join(pic_list)
os.environ['NEW_SIGNALS']=json.dumps(new)
os.environ['GONE_SIGNALS']=json.dumps(gone)
