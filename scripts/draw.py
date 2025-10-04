import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt,mplfinance as mpf,numpy as np,pandas as pd
import akshare as ak

def temp_bar():
    """沪深300 PB 5年分位温度条（使用akshare接口）"""
    # 使用akshare获取沪深300指数历史市净率数据
    # 获取沪深300指数历史市净率数据
    try:
        print("正在获取沪深300指数历史市净率数据...")
        # 获取沪深300指数历史数据
        df = ak.index_zh_a_hist(symbol="000300", period="daily", start_date="20190101")
        print(f"沪深300指数历史数据获取成功，数据条数: {len(df)}")
        # 计算市净率（这里简化处理，实际应用中可能需要更精确的计算）
        df['pb'] = pd.to_numeric(df['市净率'], errors='coerce')
        df = df.dropna(subset=['pb'])
        
        if not df.empty:
            # 计算当前分位
            pct = df['pb'].rank(pct=True).iloc[-1]   # 当前分位
            print(f"沪深300当前PB分位: {pct}")
        else:
            # 如果没有数据，默认使用0.5
            print("沪深300指数无有效市净率数据，默认使用0.5")
            pct = 0.5
    except Exception as e:
        print(f"获取沪深300市净率数据时出错: {e}")
        # 出错时默认使用0.5
        pct = 0.5
    
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
    try:
        start = (end-pd.Timedelta(weeks=50)).strftime('%Y%m%d')
        print(f"正在获取股票 {ts_code} ({name}) 的历史数据...")
        # 使用akshare获取股票历史数据
        df = ak.stock_zh_a_hist(symbol=ts_code, period="daily", start_date=start, end_date=end.strftime('%Y%m%d'))
        print(f"股票 {ts_code} 历史数据获取成功，数据条数: {len(df)}")
        if df.empty:
            print(f"股票 {ts_code} 无历史数据")
            return f"{ts_code}.png"  # 返回默认文件名
            
        df = df.sort_values('日期')
        # 重命名列以匹配原代码
        df = df.rename(columns={'日期': 'trade_date', '开盘': 'open', '最高': 'high', '最低': 'low', '收盘': 'close', '成交量': 'vol'})
        df[['open','high','low','close','vol']] = df[['open','high','low','close','vol']].astype(float)
        df['ma50'] = df['close'].rolling(50).mean()
        df['ma200'] = df['close'].rolling(200).mean()
        df.index = pd.to_datetime(df['trade_date'])
        highlight = df.iloc[-1].name   # 触发日
        ap = [mpf.make_addplot(df[['ma50','ma200']]),mpf.make_addplot(df['close'],type='scatter',markersize=30,marker='^',color='red')]
        path = f'{ts_code}.png'
        mpf.plot(df,type='candle',addplot=ap,figratio=(4,3),figscale=0.9,title=f'{name} 周K',savefig=path)
        print(f"股票 {ts_code} K线图生成成功")
        return path
    except Exception as e:
        print(f"绘制股票 {ts_code} K线图时出错: {e}")
        # 出错时创建一个空的图像文件
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, f'Error plotting {name}', ha='center', va='center')
        path = f'{ts_code}.png'
        plt.savefig(path)
        plt.close()
        return path