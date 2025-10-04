import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import json,pandas as pd,datetime as dt,numpy as np
import akshare as ak
from draw import temp_bar,plot_kline

# 获取当前日期和最近的周五
today = dt.date.today()
# 计算最近的周五
days_since_friday = (today.weekday() - 4) % 7
friday = today if days_since_friday == 0 else today - dt.timedelta(days=days_since_friday)
print(f"当前日期: {today}, 选股日期: {friday}")

# 1. 严格选股逻辑
print("开始执行严格选股逻辑...")

## 1. 基础池：剔除次新、ST
print("步骤1: 构建基础股票池（剔除次新、ST股）")
# 获取A股股票代码和名称
print("正在获取A股股票代码和名称...")
basic = ak.stock_info_a_code_name()          # ts_code,name
print(f"获取到 {len(basic)} 只A股股票")

# 获取行业分类信息
# 使用 ak.stock_board_industry_name_em() 获取行业板块名称
print("正在获取行业板块名称...")
industry_names = ak.stock_board_industry_name_em()
print(f"获取到 {len(industry_names)} 个行业板块")

# 批量获取所有行业的成分股信息
print("批量获取行业成分股信息...")
industry_mapping = {}
# 去除行业数量限制，处理所有行业
for idx, row in industry_names.iterrows():
    try:
        symbol_code = str(row['板块代码'])
        print(f"正在获取行业 {row['板块名称']} ({symbol_code}) 的成分股...")
        # 批量获取行业成分股
        cons = ak.stock_board_industry_cons_em(symbol=symbol_code)
        print(f"行业 {row['板块名称']} 成分股数量: {len(cons)}")
        for _, stock in cons.iterrows():
            industry_mapping[str(stock['名称'])] = str(row['板块名称'])
        # 添加延时以避免请求过于频繁
        # time.sleep(0.1)
    except Exception as e:
        print(f"获取行业 {row['板块名称']} 成分股时出错: {e}")
        continue

# 创建行业分类DataFrame
indus_data = []
for name, industry in industry_mapping.items():
    indus_data.append({'name': name, 'c_name': industry})
indus = pd.DataFrame(indus_data)

# 合并基本信息和行业分类
basic = basic.merge(indus, on='name', how='left')
basic = basic.rename(columns={'code':'ts_code','c_name':'industry'})
basic = basic[basic.ts_code.str.endswith(('SH','SZ'))]   # 只留A股
basic['market'] = basic.ts_code.str[-2:].map({'SH':'主板','SZ':'主板'})

print(f"基础池构建完成，共 {len(basic)} 只股票")

## 2. 获取股票估值和财务指标数据
print("步骤2: 获取股票估值和财务指标数据")

# 批量获取所有股票的实时行情数据（包含市净率）
print("正在获取所有股票的实时行情数据...")
spot_data = ak.stock_zh_a_spot_em()
print(f"获取到 {len(spot_data)} 只股票的实时行情数据")

# 选择需要的列并重命名
pb_df = spot_data[['代码', '市净率']].copy()
pb_df = pb_df.rename(columns={'代码': 'ts_code', '市净率': 'pb'})  # type: ignore
# 过滤掉市净率为 '-' 的股票
pb_filter_condition = pb_df['pb'] != '-'
pb_df = pb_df[pb_filter_condition]
pb_df['pb'] = pd.to_numeric(pb_df['pb'], errors='coerce')
print(f"获取到 {len(pb_df)} 只股票的市净率数据")

# 估算5年PB分位数（简化处理，实际应用中可以使用更精确的方法）
# 这里我们使用当前PB在历史上的分位数作为近似
pb_col = pb_df['pb']
pb_list = list(pb_col)
pb_series = pd.Series(pb_list)
rank_result = pb_series.rank(pct=True)
pb_df['pb_5y_percentile'] = rank_result * 100

# 批量获取财务指标数据（ROE和负债率）
print("批量获取财务指标数据...")
# 为了提高效率，我们只处理基础池中的股票，并与市净率数据取交集
# 先合并基础池和市净率数据，减少需要处理的股票数量
pb_codes_series = pb_df['ts_code']
pb_codes_df = pd.DataFrame({'ts_code': pb_codes_series})
basic_with_pb = basic.merge(pb_codes_df, on='ts_code', how='inner')
print(f"需要获取财务数据的股票数量: {len(basic_with_pb)}")

financial_data_list = []
success_count = 0
error_count = 0

for idx, row in basic_with_pb.iterrows():
    try:
        stock_code = str(row['ts_code'])
        print(f"正在获取股票 {stock_code} 的财务数据...")
        # 获取单只股票的财务摘要数据
        fin_data = ak.stock_financial_abstract(symbol=stock_code)
        if not fin_data.empty:
            print(f"股票 {stock_code} 财务数据获取成功，数据条数: {len(fin_data)}")
            # 提取最新的ROE和负债率数据
            latest_fin = fin_data.iloc[0]  # 取最新一期数据
            roe_value = latest_fin.get('净资产收益率', 0)
            debt_value = latest_fin.get('资产负债率', 0)
            
            financial_data_list.append({
                'ts_code': stock_code,
                'roe': float(roe_value) if roe_value and str(roe_value) != '' else 0,
                'debt_to_assets': float(debt_value) if debt_value and str(debt_value) != '' else 0
            })
            success_count += 1
        else:
            print(f"股票 {stock_code} 无财务数据")
    except Exception as e:
        error_count += 1
        if error_count <= 5:  # 只打印前5个错误
            print(f"获取股票 {row['ts_code']} 财务数据时出错: {e}")
        continue

print(f"成功获取 {success_count} 只股票的财务数据，失败 {error_count} 只")

latest = pd.DataFrame(financial_data_list)
print(f"获取到 {len(latest)} 只股票的财务指标数据")

# 批量获取月线行情数据
print("批量获取月线行情数据...")
# 去除股票数量限制，处理所有已获取到财务数据的股票
financial_stocks = latest['ts_code'].tolist()
print(f"需要获取月线数据的股票数量: {len(financial_stocks)}")

monthly_data_list = []
success_count = 0
error_count = 0

for stock_code in financial_stocks:
    try:
        print(f"正在获取股票 {stock_code} 的月线数据...")
        # 批量获取月线数据
        monthly_data = ak.stock_zh_a_hist(symbol=stock_code, period="monthly", end_date=friday.strftime('%Y%m%d'))
        if not monthly_data.empty:
            print(f"股票 {stock_code} 月线数据获取成功，数据条数: {len(monthly_data)}")
            latest_month = monthly_data.iloc[-1]  # 取最近一个月的数据
            monthly_data_list.append({
                'ts_code': stock_code,
                'close': float(latest_month['收盘']),
                'vol': float(latest_month['成交量']),
                'amount': float(latest_month['成交额'])
            })
            success_count += 1
        else:
            print(f"股票 {stock_code} 无月线数据")
    except Exception as e:
        error_count += 1
        if error_count <= 5:  # 只打印前5个错误
            print(f"获取股票 {stock_code} 月线数据时出错: {e}")
        continue

print(f"成功获取 {success_count} 只股票的月线数据，失败 {error_count} 只")

monthly = pd.DataFrame(monthly_data_list)
print(f"获取到 {len(monthly)} 只股票的月线行情数据")

## 3. 合并指标
print("步骤3: 合并所有指标数据")
# 合并所有数据
df_basic = pd.DataFrame(basic)
df_pb = pd.DataFrame(pb_df)
df_latest = pd.DataFrame(latest)
df_monthly = pd.DataFrame(monthly)
df = df_basic.merge(df_pb, on='ts_code', how='left').merge(df_latest, on='ts_code', how='left').merge(df_monthly, on='ts_code', how='left')
# 删除关键字段为空的行
dropna_subset = ['pb','roe','debt_to_assets']
df = df.dropna(subset=dropna_subset)
print(f"合并后共有 {len(df)} 只股票")

## 4. 严格档条件筛选
print("步骤4: 应用严格档筛选条件")
# 计算行业成交额排名
has_amount_column = 'amount' in df.columns
if has_amount_column:
    amount_col = df['amount']
    is_notna = pd.notna(amount_col)
    has_valid_amount = True if any(list(is_notna)) else False
    if has_valid_amount:
        groupby_obj = df.groupby('industry')
        amount_series = df['amount']
        rank_result = groupby_obj['amount'].rank(ascending=False, method='min')
        df['industry_rank'] = rank_result

        # 应用筛选条件
        # 1. PB<1
        # 2. ROE>12%
        # 3. 负债率<50%
        # 4. 5年PB分位数<20
        # 5. 行业成交额TOP3
        pb_condition = df['pb']<1
        roe_condition = df['roe']>12
        debt_condition = df['debt_to_assets']<50
        pb_percentile_condition = df['pb_5y_percentile']<20
        industry_condition = df['industry_rank']<=3
        condition = pb_condition & roe_condition & debt_condition & pb_percentile_condition & industry_condition
        filtered_df = df[condition]
        print(f"严格档筛选后剩余 {len(filtered_df)} 只股票")
    else:
        print("成交额数据全为空，跳过行业排名筛选")
        pb_condition = df['pb']<1
        roe_condition = df['roe']>12
        debt_condition = df['debt_to_assets']<50
        pb_percentile_condition = df['pb_5y_percentile']<20
        condition = pb_condition & roe_condition & debt_condition & pb_percentile_condition
        filtered_df = df[condition]
        print(f"基础筛选后剩余 {len(filtered_df)} 只股票")
else:
    print("缺少成交额数据，跳过行业排名筛选")
    pb_condition = df['pb']<1
    roe_condition = df['roe']>12
    debt_condition = df['debt_to_assets']<50
    pb_percentile_condition = df['pb_5y_percentile']<20
    condition = pb_condition & roe_condition & debt_condition & pb_percentile_condition
    filtered_df = df[condition]
    print(f"基础筛选后剩余 {len(filtered_df)} 只股票")

## 5. 底部放量：20 日量比 >2（用月线 vol 估算）
print("步骤5: 检查底部放量条件")
# 批量估算前一个月的成交量
print("批量获取前期月线数据...")
# 去除股票数量限制，处理所有筛选后的股票
if not filtered_df.empty:
    filtered_stocks = filtered_df['ts_code'].tolist()
    print(f"需要获取前期月线数据的股票数量: {len(filtered_stocks)}")
    
    prev_vol_data_list = []
    success_count = 0
    error_count = 0

    for stock_code in filtered_stocks:
        try:
            print(f"正在获取股票 {stock_code} 的前期月线数据...")
            prev_date = friday - dt.timedelta(days=35)
            # 批量获取两个月前的数据
            prev_month_data = ak.stock_zh_a_hist(symbol=stock_code, period="monthly", end_date=prev_date.strftime('%Y%m%d'))
            if not prev_month_data.empty:
                print(f"股票 {stock_code} 前期月线数据获取成功，数据条数: {len(prev_month_data)}")
                prev_month = prev_month_data.iloc[-1]  # 取最近一个月的数据
                prev_vol_data_list.append({
                    'ts_code': stock_code,
                    'prev_vol': float(prev_month['成交量'])
                })
                success_count += 1
            else:
                print(f"股票 {stock_code} 无前期月线数据")
        except Exception as e:
            error_count += 1
            if error_count <= 5:  # 只打印前5个错误
                print(f"获取股票 {stock_code} 前期月线数据时出错: {e}")
            continue

    print(f"成功获取 {success_count} 只股票的前期月线数据，失败 {error_count} 只")

    if len(prev_vol_data_list) > 0:
        prev_vol = pd.DataFrame(prev_vol_data_list)
        prev_vol.columns = ['ts_code','prev_vol']

        # 合并数据并计算量比
        if not filtered_df.empty and not prev_vol.empty:
            filtered_df = filtered_df.merge(prev_vol, on='ts_code', how='left')
            vol_col = filtered_df['vol']
            prev_vol_col = filtered_df['prev_vol']
            filtered_df['vol_ratio'] = vol_col / prev_vol_col
            vol_ratio_condition = filtered_df['vol_ratio'] >= 2.0
            filtered_df = filtered_df[vol_ratio_condition]
            print(f"底部放量筛选后剩余 {len(filtered_df)} 只股票")
        else:
            print("无数据可用于底部放量筛选")
    else:
        print("无前期成交量数据")
else:
    print("无筛选后的股票，跳过底部放量检查")

## 6. 生成说明
if filtered_df.empty:
    print('本周无严格档信号')
    os.environ['HAS_PICK'] = 'false'
else:
    print(f"生成选股结果，共 {len(filtered_df)} 只股票")
    filtered_df['logic'] = ( '1) PB<1 & ROE>12% & 负债<50% 且处于近5年PB低位；'
                    '2) 行业成交额TOP3龙头；3) 20日量比≥2，底部温和放量。')
    name_col = filtered_df['name']
    ts_code_col = filtered_df['ts_code']
    industry_col = filtered_df['industry']
    pb_col = filtered_df['pb']
    roe_col = filtered_df['roe']
    vol_ratio_col = filtered_df['vol_ratio']
    pb_rounded = pb_col.round(2).astype(str)
    roe_rounded = roe_col.round(1).astype(str)
    vol_ratio_rounded = vol_ratio_col.round(1).astype(str)
    key_info_template = (name_col+'('+ts_code_col+') | 行业:'+industry_col+
                      ' | PB:'+pb_rounded+
                      ' | ROE:'+roe_rounded+'%'+
                      ' | 量比:'+vol_ratio_rounded)
    filtered_df['key_info'] = key_info_template
    filtered_df.to_csv('pick.csv', index=False, encoding='utf-8-sig')
    os.environ['HAS_PICK'] = 'true'
    print("选股结果已保存到 pick.csv")

# 2. 画沪深300估值温度条
print("步骤7: 生成沪深300估值温度条")
# 使用修改后的 temp_bar 函数（基于 akshare）
temp_img = temp_bar()

# 3. 画个股K线 & 保存
print("步骤8: 生成个股K线图")
pic_list = []
if not filtered_df.empty:
    for idx, row in filtered_df.iterrows():
        try:
            stock_code = str(row['ts_code'])
            stock_name = str(row['name'])
            pic = plot_kline(stock_code, stock_name, end=friday)
            if pic:  # 检查返回值是否有效
                pic_list.append(pic)
            print(f"已生成 {stock_name} 的K线图")
        except Exception as e:
            print(f"生成 {row['name']} 的K线图时出错: {e}")

# 4. cache对比
print("步骤9: 对比历史选股结果")
os.makedirs('cache', exist_ok=True)
curr = []
if not filtered_df.empty:
    select_cols = ['ts_code','name']
    records_data = filtered_df[select_cols]
    # 转换为字典列表
    curr = []
    for i in range(len(records_data)):
        row_series = records_data.iloc[i]  # type: ignore
        ts_code_val = str(row_series['ts_code'])
        name_val = str(row_series['name'])
        row_dict = {
            'ts_code': ts_code_val,
            'name': name_val
        }
        curr.append(row_dict)
last = []
if os.path.exists('cache/last_pick.json'):
    try:
        with open('cache/last_pick.json', 'r', encoding='utf-8') as f:
            data = f.read()
            if data:
                last = json.loads(data)
            else:
                last = []
    except Exception as e:
        print(f"读取历史选股结果时出错: {e}")
        last = []
new  = [c for c in curr if c['ts_code'] not in [l['ts_code'] for l in last]]
gone = [l for l in last if l['ts_code'] not in [c['ts_code'] for c in curr]]
try:
    with open('cache/last_pick.json', 'w', encoding='utf-8') as f:
        json.dump(curr, f, ensure_ascii=False)
except Exception as e:
    print(f"保存选股结果时出错: {e}")
print(f"新增信号: {len(new)} 只, 剔除信号: {len(gone)} 只")

# 5. 环境变量传给mail.py
os.environ['HAS_PICK'] = 'true' if not filtered_df.empty else 'false'
os.environ['TEMP_PIC'] = temp_img
os.environ['KLINE_PICS'] = ','.join(pic_list)
os.environ['NEW_SIGNALS'] = json.dumps(new, ensure_ascii=False)
os.environ['GONE_SIGNALS'] = json.dumps(gone, ensure_ascii=False)

print("选股流程执行完成")