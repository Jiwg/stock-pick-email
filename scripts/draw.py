import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt,mplfinance as mpf,numpy as np,pandas as pd,tushare as ts

def temp_bar(pro):
    """沪深300 PB 5年分位温度条"""
    df = pro.index_dailybasic(ts_code='399300.SZ',fields='trade_date,pb',start_date='20190101')
    df['pb'] = df['pb'].astype(float)
    pct = df['pb'].rank(pct=True).iloc[-1]   # 当前分位
    fig,ax = plt.subplots(figsize=(3,0.6))
    ax.barh([0],[pct],color='red' if pct>0.8 else 'orange' if pct>0.5 else 'green')
    ax.set_xlim(0,1);ax.set_yticks([]);ax.set_xticks([])
    ax.text(0.5,-0.3,f'沪深300  PB温度 {pct*100:.0f}%',ha='center',fontsize=10)
    path='temp_bar.png'
    plt.savefig(path,bbox_inches='tight',dpi=120)
    plt.close()
    return path

def plot_kline(ts_code,name,end):
    """最近50周K线+50/200周均线+触发点高亮"""
    start = (end-pd.Timedelta(weeks=50)).strftime('%Y%m%d')
    df = ts.pro_bar(ts_code=ts_code,asset='E',freq='W',start_date=start,end_date=end.strftime('%Y%m%d'))
    df = df.sort_values('trade_date')
    df[['open','high','low','close','vol']] = df[['open','high','low','close','vol']].astype(float)
    df['ma50'] = df['close'].rolling(50).mean()
    df['ma200'] = df['close'].rolling(200).mean()
    df.index = pd.to_datetime(df['trade_date'])
    highlight = df.iloc[-1].name   # 触发日
    ap = [mpf.make_addplot(df[['ma50','ma200']]),mpf.make_addplot(df['close'],type='scatter',markersize=30,marker='^',color='red')]
    path = f'{ts_code}.png'
    mpf.plot(df,type='candle',addplot=ap,figratio=(4,3),figscale=0.9,title=f'{name} 周K',savefig=path)
    return path