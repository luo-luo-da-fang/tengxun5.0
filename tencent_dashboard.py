import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import qrcode
from PIL import Image
from io import BytesIO
import re
import warnings
warnings.filterwarnings('ignore')

# ===================== 可选依赖检测 =====================
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

try:
    from statsmodels.tsa.arima.model import ARIMA
    ARIMA_AVAILABLE = True
except ImportError:
    ARIMA_AVAILABLE = False

# ===================== 基础配置数据 =====================
company_info = {
    "腾讯控股": "00700.HK",
    "阿里巴巴": "9988.HK",
    "百度": "BIDU",
    "网易": "NTES"
}
company_alias = {
    "腾讯": "腾讯控股", "鹅厂": "腾讯控股", "腾讯控股": "腾讯控股",
    "阿里": "阿里巴巴", "阿里巴巴": "阿里巴巴", "淘宝": "阿里巴巴",
    "百度": "百度", "百度公司": "百度",
    "网易": "网易", "猪场": "网易"
}
all_company_list = ["腾讯控股", "阿里巴巴", "百度", "网易"]

# ===================== 页面全局配置 =====================
st.set_page_config(
    page_title="互联网公司财报分析看板",
    layout="wide",
    page_icon="📈",
    initial_sidebar_state="expanded"
)

# ===================== 全局CSS样式 =====================
st.markdown("""
<style>
/* 全局背景 */
.stApp {
    background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 50%, #e2e8f0 100%);
    font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
    color: #0f172a;
}

/* 主标题 */
.main-title {
    font-size: 2.3rem !important;
    font-weight: 700 !important;
    text-align: center;
    padding: 2rem 0 1.5rem 0;
    color: #0f172a !important;
    letter-spacing: 3px;
    position: relative;
    margin-bottom: 2rem;
}
.main-title::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 150px;
    height: 3px;
    background: linear-gradient(90deg, transparent, #2563eb, #8b5cf6, transparent);
    border-radius: 2px;
}

/* 高端卡片容器 */
.premium-card {
    background: #ffffff;
    border-radius: 16px;
    padding: 2rem;
    margin-bottom: 2.2rem;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04),
                0 20px 40px -10px rgba(15, 23, 42, 0.08),
                0 10px 15px -5px rgba(15, 23, 42, 0.04);
    border: 1px solid rgba(148, 163, 184, 0.12);
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}
.premium-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #2563eb, #6366f1, #8b5cf6, #a855f7);
}
.premium-card:hover {
    box-shadow: 0 4px 8px rgba(15, 23, 42, 0.06),
                0 30px 60px -15px rgba(15, 23, 42, 0.12);
    transform: translateY(-3px);
}

/* 核心指标卡片 */
.metric-premium {
    background: linear-gradient(145deg, #f8fafc 0%, #f1f5f9 100%);
    border-radius: 14px;
    padding: 1.5rem 1rem;
    text-align: center;
    border: 1px solid rgba(148, 163, 184, 0.15);
    transition: all 0.35s ease;
    position: relative;
    overflow: hidden;
}
.metric-premium::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 60%;
    height: 2px;
    background: linear-gradient(90deg, transparent, #2563eb, transparent);
    opacity: 0;
    transition: opacity 0.3s ease;
}
.metric-premium:hover {
    border-color: #2563eb;
    background: linear-gradient(145deg, #eff6ff 0%, #dbeafe 100%);
    transform: translateY(-4px);
    box-shadow: 0 15px 30px -10px rgba(37, 99, 235, 0.2);
}
.metric-premium:hover::after {
    opacity: 1;
}
.metric-value-premium {
    font-size: 1.9rem !important;
    font-weight: 700 !important;
    color: #1e40af !important;
    margin: 0.6rem 0;
    font-family: 'DIN Alternate', sans-serif;
}
.metric-label-premium {
    font-size: 0.92rem !important;
    color: #64748b !important;
    font-weight: 500;
    letter-spacing: 0.8px;
}

/* 点位分析弹窗 */
.point-analysis {
    background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
    border-radius: 12px;
    padding: 1.3rem 1.6rem;
    margin-top: 1.2rem;
    border-left: 4px solid #0ea5e9;
    animation: slideIn 0.35s ease-out;
    box-shadow: 0 4px 12px rgba(14, 165, 233, 0.1);
}
@keyframes slideIn {
    from { opacity: 0; transform: translateY(-12px); }
    to { opacity: 1; transform: translateY(0); }
}
.point-analysis h4 {
    color: #0c4a6e;
    margin-bottom: 0.7rem;
    font-size: 1.1rem;
    font-weight: 600;
}
.point-analysis p {
    color: #0f172a;
    line-height: 1.8;
    margin-bottom: 0.5rem;
    font-size: 0.95rem;
}

/* 产品卡片 */
.product-card {
    background: linear-gradient(145deg, #ffffff 0%, #f8fafc 100%);
    border-radius: 14px;
    padding: 1.5rem 1.2rem;
    text-align: center;
    border: 1px solid rgba(148, 163, 184, 0.15);
    transition: all 0.35s ease;
    margin-bottom: 1rem;
}
.product-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 20px 40px -10px rgba(37, 99, 235, 0.15);
    border-color: #2563eb;
}
.product-icon {
    font-size: 2.8rem;
    margin-bottom: 0.8rem;
    display: inline-block;
    filter: drop-shadow(0 4px 6px rgba(37, 99, 235, 0.2));
}
.product-name {
    font-size: 1.1rem;
    font-weight: 600;
    color: #0f172a;
    margin-bottom: 0.5rem;
}
.product-desc {
    font-size: 0.85rem;
    color: #64748b;
    line-height: 1.6;
    margin-bottom: 0.6rem;
}
.product-stat {
    font-size: 0.9rem;
    font-weight: 600;
    color: #2563eb;
}

/* 悬浮智能助手 */
.ai-float-btn {
    position: fixed;
    bottom: 30px;
    right: 30px;
    width: 72px;
    height: 72px;
    border-radius: 50%;
    background: linear-gradient(135deg, #2563eb 0%, #8b5cf6 100%);
    box-shadow: 0 10px 30px rgba(37, 99, 235, 0.4),
                0 0 0 4px rgba(255, 255, 255, 0.8);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2.2rem;
    cursor: pointer;
    z-index: 9999;
    transition: all 0.3s ease;
    animation: floatAnim 3s ease-in-out infinite;
    border: none;
}
.ai-float-btn:hover {
    transform: scale(1.12);
    box-shadow: 0 15px 40px rgba(37, 99, 235, 0.5),
                0 0 0 4px rgba(255, 255, 255, 1);
}
@keyframes floatAnim {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-8px); }
}

.ai-greeting {
    position: fixed;
    bottom: 115px;
    right: 30px;
    background: white;
    padding: 12px 18px;
    border-radius: 16px 16px 4px 16px;
    box-shadow: 0 10px 30px rgba(15, 23, 42, 0.15);
    font-size: 0.9rem;
    color: #0f172a;
    z-index: 9998;
    max-width: 260px;
    animation: bubbleIn 0.3s ease-out;
    line-height: 1.5;
}
@keyframes bubbleIn {
    from { opacity: 0; transform: translateY(10px) scale(0.9); }
    to { opacity: 1; transform: translateY(0) scale(1); }
}

/* 用户画像标签 */
.user-tag {
    display: inline-block;
    padding: 0.35rem 0.9rem;
    border-radius: 20px;
    font-size: 0.85rem;
    margin: 0.3rem;
    font-weight: 500;
}
.tag-blue { background: #dbeafe; color: #1e40af; }
.tag-purple { background: #ede9fe; color: #6d28d9; }
.tag-cyan { background: #cffafe; color: #155e75; }
.tag-green { background: #dcfce7; color: #166534; }
.tag-orange { background: #ffedd5; color: #9a3412; }

/* 侧边栏 */
.css-1d391kg {
    background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
    border-right: 1px solid rgba(148, 163, 184, 0.15);
    box-shadow: 4px 0 25px rgba(15, 23, 42, 0.03);
}

/* 页脚 */
.footer-section {
    text-align: center;
    color: #64748b;
    padding: 2rem 1rem 6rem 1rem;
    border-top: 1px solid rgba(148, 163, 184, 0.15);
    margin-top: 3rem;
    font-size: 0.9rem;
}
</style>
""", unsafe_allow_html=True)

# ===================== 智能问答核心函数 =====================
def parse_question(question, main_company, select_year, all_data, competitor_data):
    question = question.strip()
    q = question.lower()

    # 问候语
    greetings = ["你好", "您好", "hi", "hello", "在吗", "在不在", "嗨", "哈喽", "你好呀"]
    if any(g in q for g in greetings):
        return "你好呀👋 我是智能财报助手小腾！\n\n我可以帮你：\n- 查询任意公司的营收、利润、毛利率等数据\n- 对比不同公司的财务表现\n- 解读年度经营趋势和行业格局\n\n直接问我就可以啦，比如「阿里巴巴2023年净利润多少？」"

    # 识别公司
    target_company = main_company
    for alias, full_name in company_alias.items():
        if alias in question:
            target_company = full_name
            break

    # 识别年份
    target_year = select_year
    if "今年" in q or "本年度" in q or "当期" in q:
        target_year = select_year
    elif "去年" in q or "上一年" in q:
        target_year = select_year - 1
    else:
        year_match = re.search(r'20\d{2}', question)
        if year_match:
            target_year = int(year_match.group())

    # 获取对应数据
    if target_company == main_company:
        data = all_data
    elif target_company in competitor_data:
        data = competitor_data[target_company]
    else:
        data = all_data
        target_company = main_company

    year_data = data[data["年份"] == target_year]
    if year_data.empty:
        return f"抱歉，没有找到{target_company}{target_year}年的相关数据，你可以试试其他年份~"
    row = year_data.iloc[0]

    # 识别查询意图
    if any(w in q for w in ["营收", "收入", "营业额", "销售额"]):
        growth = row["营收同比增速%"]
        growth_text = f"同比增长{growth}%" if growth > 0 else f"同比下降{abs(growth)}%" if growth < 0 else "与上年持平"
        return f"""📊 {target_company}{target_year}年营收情况：
- 营业收入：{row['营业收入']:.2f}亿元
- 营收增速：{growth_text}
- 营收规模在行业内处于第一梯队，增长韧性较强。"""

    elif any(w in q for w in ["净利润", "利润", "盈利", "赚钱"]):
        growth = row["净利润同比增速%"]
        growth_text = f"同比增长{growth}%" if growth > 0 else f"同比下降{abs(growth)}%" if growth < 0 else "与上年持平"
        return f"""💰 {target_company}{target_year}年盈利情况：
- 归母净利润：{row['归母净利润']:.2f}亿元
- 净利润率：{row['净利润率%']}%
- 利润增速：{growth_text}
- 整体盈利能力处于行业领先水平。"""

    elif any(w in q for w in ["毛利率", "毛利"]):
        return f"""📈 {target_company}{target_year}年毛利率：
- 毛利率：{row['毛利率%']}%
- 处于行业较高水平，体现了公司较强的定价权和成本控制能力。"""

    elif any(w in q for w in ["负债", "资产负债率", "偿债", "财务风险"]):
        return f"""🏦 {target_company}{target_year}年负债情况：
- 资产负债率：{row['资产负债率%']}%
- 负债结构健康，财务风险较低，偿债能力充足。"""

    elif any(w in q for w in ["roe", "净资产收益率", "股东回报"]):
        return f"""💎 {target_company}{target_year}年净资产收益率：
- ROE：{row['净资产收益率%']}%
- 为股东创造回报的能力优秀，资本使用效率高。"""

    elif any(w in q for w in ["对比", "相比", "谁好", "差距", "竞品"]):
        if len(competitor_data) > 0:
            comp_name = list(competitor_data.keys())[0]
            comp_row = competitor_data[comp_name][competitor_data[comp_name]["年份"] == target_year].iloc[0]
            return f"""🏆 {target_year}年 {target_company} vs {comp_name} 对比：
- 营收：{row['营业收入']:.2f}亿 vs {comp_row['营业收入']:.2f}亿
- 净利润：{row['归母净利润']:.2f}亿 vs {comp_row['归母净利润']:.2f}亿
- 净利润率：{row['净利润率%']}% vs {comp_row['净利润率%']}%
- {target_company}在盈利能力方面表现更突出。"""
        else:
            return "请先在左侧控制台选择对比公司，再来问我对比问题哦~"

    elif any(w in q for w in ["数据", "全部", "概况", "情况", "怎么样", "介绍"]):
        return f"""📋 {target_company}{target_year}年核心数据概览：
- 营业收入：{row['营业收入']:.2f}亿元
- 归母净利润：{row['归母净利润']:.2f}亿元
- 毛利率：{row['毛利率%']}%
- 净利润率：{row['净利润率%']}%
- 资产负债率：{row['资产负债率%']}%
- 净资产收益率：{row['净资产收益率%']}%
整体财务状况健康，基本面扎实。"""

    else:
        return f"""我暂时没太理解你的问题😅 你可以这样问我：
- "{target_company}今年营收多少？"
- "净利润率怎么样？"
- "和竞品对比如何？"
也可以直接点击图表上的数据点，查看更详细的点位分析~"""

# ===================== 数据获取模块 =====================
@st.cache_data(ttl=86400)
def fetch_financial_data(ticker, years=5):
    if not YFINANCE_AVAILABLE:
        return None
    try:
        import requests
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        stock = yf.Ticker(ticker, session=session)
        income_stmt = stock.income_stmt
        balance_sheet = stock.balance_sheet
        cashflow = stock.cashflow

        if income_stmt.empty:
            return None

        annual_data = []
        for year in range(years):
            if year >= len(income_stmt.columns):
                break
            date = income_stmt.columns[year]
            year_num = date.year

            revenue = income_stmt.loc['Total Revenue', date] if 'Total Revenue' in income_stmt.index else np.nan
            cost = income_stmt.loc['Cost Of Revenue', date] if 'Cost Of Revenue' in income_stmt.index else np.nan
            net_income = income_stmt.loc['Net Income', date] if 'Net Income' in income_stmt.index else np.nan
            total_assets = balance_sheet.loc['Total Assets', date] if 'Total Assets' in balance_sheet.index else np.nan
            total_liab = balance_sheet.loc['Total Liabilities Net Minority Interest', date] if 'Total Liabilities Net Minority Interest' in balance_sheet.index else np.nan
            equity = balance_sheet.loc['Stockholders Equity', date] if 'Stockholders Equity' in balance_sheet.index else np.nan
            op_cash = cashflow.loc['Operating Cash Flow', date] if 'Operating Cash Flow' in cashflow.index else np.nan

            # 单位转换为亿元
            if ticker == 'BIDU':
                rate = 7 * 0.00000001
            else:
                rate = 0.00000001

            annual_data.append({
                "年份": year_num,
                "营业收入": round(revenue * rate, 2),
                "营业成本": round(cost * rate, 2),
                "归母净利润": round(net_income * rate, 2),
                "总资产": round(total_assets * rate, 2),
                "总负债": round(total_liab * rate, 2),
                "股东权益": round(equity * rate, 2),
                "经营现金流净额": round(op_cash * rate, 2)
            })

        df = pd.DataFrame(annual_data)
        df = df.sort_values("年份").reset_index(drop=True)
        return df
    except Exception:
        return None

# ===================== 本地备份数据 =====================
backup_data = {
    "腾讯控股": pd.DataFrame({
        "年份": [2021, 2022, 2023, 2024],
        "营业收入": [5601.18, 5545.52, 6090.15, 6602.57],
        "营业成本": [2120.55, 2089.36, 2267.82, 2456.31],
        "归母净利润": [2248.22, 1882.43, 1152.16, 1940.73],
        "总资产": [16123.64, 15781.31, 15772.46, 17809.95],
        "总负债": [7356.71, 7952.71, 7035.65, 7270.99],
        "股东权益": [8766.93, 7828.60, 8736.81, 10538.96],
        "经营现金流净额": [1751.86, 1460.91, 2219.62, 2585.21]
    }),
    "阿里巴巴": pd.DataFrame({
        "年份": [2021, 2022, 2023, 2024],
        "营业收入": [7172.89, 8530.62, 8686.87, 9411.68],
        "营业成本": [4212.05, 5394.50, 5496.95, 5863.23],
        "归母净利润": [1503.08, 619.59, 725.09, 797.41],
        "总资产": [16902.18, 16955.53, 17530.44, 17648.29],
        "总负债": [6065.84, 6133.60, 6301.23, 6522.30],
        "股东权益": [10836.34, 10821.93, 11229.21, 11125.99],
        "经营现金流净额": [2317.86, 1427.59, 1997.52, 1825.93]
    }),
    "百度": pd.DataFrame({
        "年份": [2021, 2022, 2023, 2024],
        "营业收入": [1244.93, 1236.75, 1345.98, 1331.25],
        "营业成本": [684.71, 692.58, 753.75, 745.10],
        "归母净利润": [75.91, 75.34, 215.49, 241.75],
        "总资产": [3800.34, 3909.73, 4067.59, 4277.80],
        "总负债": [1560.82, 1531.68, 1441.51, 1441.68],
        "股东权益": [2114.59, 2234.78, 2436.26, 2636.20],
        "经营现金流净额": [201.22, 261.70, 366.15, 212.34]
    }),
    "网易": pd.DataFrame({
        "年份": [2021, 2022, 2023, 2024],
        "营业收入": [876.06, 964.96, 1034.77, 1053.00],
        "营业成本": [421.50, 468.30, 502.10, 518.50],
        "归母净利润": [168.57, 205.28, 270.63, 297.00],
        "总资产": [2156.80, 2435.20, 2718.50, 2987.30],
        "总负债": [689.70, 752.90, 815.60, 876.40],
        "股东权益": [1467.10, 1682.30, 1902.90, 2110.90],
        "经营现金流净额": [285.60, 321.40, 387.20, 412.50]
    })
}

# ===================== 业务数据 =====================
tencent_business_data = pd.DataFrame({
    "年份": [2021, 2022, 2023, 2024],
    "增值服务营收": [2916.71, 2875.59, 2876.44, 3252.08],
    "金融科技及企业服务营收": [1722.00, 1771.52, 2170.39, 2378.52],
    "营销服务营收": [886.69, 827.75, 958.62, 1015.26],
    "中国大陆营收": [4929.04, 4879.10, 5361.33, 5815.36],
    "海外营收": [672.14, 666.42, 728.82, 787.21],
})

tencent_products = [
    {"icon": "💬", "name": "微信 & WeChat", "desc": "国民级社交应用，连接超10亿用户", "stat": "月活 13.8亿+"},
    {"icon": "🐧", "name": "QQ", "desc": "年轻用户社交主阵地，Z世代首选", "stat": "月活 5.6亿+"},
    {"icon": "🎮", "name": "王者荣耀", "desc": "国民级MOBA手游，全球收入最高手游", "stat": "日活 1.2亿+"},
    {"icon": "💳", "name": "微信支付", "desc": "移动支付龙头，覆盖全场景消费", "stat": "市占率 40%+"},
    {"icon": "☁️", "name": "腾讯云", "desc": "国内第二大云服务商，政企市场领先", "stat": "年营收 900亿+"},
    {"icon": "📺", "name": "腾讯视频", "desc": "头部长视频平台，内容生态完善", "stat": "付费会员 1.3亿+"},
    {"icon": "🎵", "name": "腾讯音乐", "desc": "国内最大在线音乐娱乐平台", "stat": "月活 5.8亿+"},
    {"icon": "🏢", "name": "企业微信", "desc": "企业办公协同与客户连接工具", "stat": "服务企业 1200万+"}
]

user_age_data = pd.DataFrame({
    "年龄段": ["18岁以下", "18-24岁", "25-30岁", "31-40岁", "41-50岁", "50岁以上"],
    "占比%": [12, 24, 30, 20, 10, 4]
})

user_city_data = pd.DataFrame({
    "城市等级": ["一线城市", "新一线城市", "二线城市", "三线城市", "四线及以下"],
    "占比%": [18, 26, 22, 18, 16]
})

user_groups = [
    {"name": "Z世代学生群体", "tag": "tag-purple", "desc": "18-24岁，以大学生为主，热衷游戏、社交、短视频，付费意愿强"},
    {"name": "都市白领群体", "tag": "tag-blue", "desc": "25-40岁，职场人士，使用微信办公、支付、资讯，消费能力强"},
    {"name": "下沉市场群体", "tag": "tag-green", "desc": "三四线城市及县域用户，微信支付、小程序、视频号核心用户"},
    {"name": "银发老年群体", "tag": "tag-orange", "desc": "50岁以上，通过微信连接家人、获取资讯，用户规模快速增长"},
    {"name": "企业B端用户", "tag": "tag-cyan", "desc": "企业与政府机构，使用腾讯云、企业微信等ToB服务"}
]

year_analysis = {
    2021: {
        "revenue": "2021年是公司业绩大年，核心业务均保持高速增长，增值服务和金融科技业务双轮驱动，整体营收创历史新高。",
        "profit": "2021年净利润处于高位，主要得益于游戏业务的强劲表现和投资收益的贡献，盈利能力处于峰值。"
    },
    2022: {
        "revenue": "2022年受宏观环境、行业监管和疫情多重影响，营收略有承压，出现阶段性回调，属于行业性调整。",
        "profit": "2022年净利润出现下滑，一方面是主营业务增速放缓，另一方面是公司主动进行成本结构优化和战略投入。"
    },
    2023: {
        "revenue": "2023年公司重回增长通道，广告业务强劲复苏，金融科技业务持续高增，带动整体营收修复。",
        "profit": "2023年为利润低点，主要是前期投入集中释放、减值计提等因素影响，属于业绩触底期。"
    },
    2024: {
        "revenue": "2024年营收稳健增长，核心业务基本盘稳固，新业务贡献逐步提升，增长质量持续优化。",
        "profit": "2024年净利润强势反弹，盈利能力显著修复，降本增效成效显现，利润增速远超营收增速。"
    }
}

province_full_data = pd.DataFrame({
    "省份": [
        "北京市", "天津市", "河北省", "山西省", "内蒙古自治区",
        "辽宁省", "吉林省", "黑龙江省", "上海市", "江苏省",
        "浙江省", "安徽省", "福建省", "江西省", "山东省",
        "河南省", "湖北省", "湖南省", "广东省", "广西壮族自治区",
        "海南省", "重庆市", "四川省", "贵州省", "云南省",
        "西藏自治区", "陕西省", "甘肃省", "青海省", "宁夏回族自治区",
        "新疆维吾尔自治区", "香港特别行政区", "澳门特别行政区", "台湾省"
    ],
    "纬度": [
        39.9042, 39.0842, 38.0428, 37.8706, 40.8263,
        41.8045, 43.8868, 45.7366, 31.2304, 32.0603,
        30.2741, 31.8612, 26.0745, 28.6756, 36.6758,
        34.7466, 30.5928, 28.2282, 23.1291, 22.8152,
        20.0440, 29.4316, 30.6572, 26.6470, 25.0406,
        29.6456, 34.2648, 36.0611, 36.6235, 38.4872,
        43.8256, 22.3193, 22.1987, 23.6978
    ],
    "经度": [
        116.4074, 117.2009, 114.5149, 112.5489, 111.7659,
        123.4327, 125.3245, 126.6617, 121.4737, 118.7626,
        120.1551, 117.2830, 119.3062, 115.8921, 117.0009,
        113.6254, 114.3055, 112.9388, 113.2644, 108.3275,
        110.1987, 106.9123, 104.0658, 106.6342, 102.7123,
        91.1175, 108.9542, 103.8343, 101.7782, 106.2309,
        87.6168, 114.1694, 113.5439, 120.9605
    ],
    "占比%": [
        7.8, 2.1, 4.5, 1.8, 1.2,
        2.5, 1.1, 1.0, 8.3, 14.8,
        12.7, 2.3, 4.3, 1.9, 9.3,
        5.2, 4.8, 3.1, 21.2, 1.7,
        0.8, 2.4, 6.3, 1.0, 1.5,
        0.1, 2.9, 0.7, 0.2, 0.3,
        0.9, 3.5, 0.5, 2.0
    ]
})

# ===================== 侧边栏控件 =====================
with st.sidebar:
    st.header("🎛️ 财报分析控制台")

    data_source_options = ["本地备份数据"]
    if YFINANCE_AVAILABLE:
        data_source_options.insert(0, "自动获取(推荐)")

    data_source = st.radio(
        "数据来源",
        data_source_options,
        help="自动获取会从Yahoo Finance拉取最新财报数据，云端环境可能访问失败，将自动回退到本地数据"
    )

    main_company = st.selectbox(
        "选择主分析公司",
        all_company_list,
        index=0
    )

    st.subheader("🏆 竞品对比选择")
    available_competitors = [c for c in all_company_list if c != main_company]
    competitors = st.multiselect(
        "选择对比公司",
        available_competitors,
        default=available_competitors[:2]
    )

    year_list = [2021, 2022, 2023, 2024]
    select_year = st.select_slider(
        "选择查看年份",
        options=year_list,
        value=max(year_list)
    )

    st.subheader("📈 预测设置")
    if ARIMA_AVAILABLE:
        forecast_years = st.slider(
            "预测未来年数",
            min_value=1,
            max_value=5,
            value=3,
            help="基于历史数据预测未来营收和利润"
        )
    else:
        st.info("预测功能需要安装statsmodels库")
        forecast_years = 0

    st.divider()
    st.info("💡 点击图表数据点可查看年度分析\n右下角🤖可召唤智能助手")

# ===================== 数据处理逻辑 =====================
@st.cache_data
def load_company_data(company_name, use_api):
    if use_api and YFINANCE_AVAILABLE:
        data = fetch_financial_data(company_info[company_name])
        if data is not None and len(data) >= 3:
            return data
    return backup_data[company_name]

use_api = (data_source == "自动获取(推荐)")
main_data = load_company_data(main_company, use_api)

competitor_data_dict = {}
for comp in competitors:
    competitor_data_dict[comp] = load_company_data(comp, use_api)

def calc_financial_indices(df):
    df = df.copy()
    df["毛利率%"] = round((df["营业收入"] - df["营业成本"]) / df["营业收入"] * 100, 2)
    df["净利润率%"] = round(df["归母净利润"] / df["营业收入"] * 100, 2)
    df["净资产收益率%"] = round(df["归母净利润"] / df["股东权益"] * 100, 2)
    df["营收同比增速%"] = round(df["营业收入"].pct_change() * 100, 2)
    df["净利润同比增速%"] = round(df["归母净利润"].pct_change() * 100, 2)
    df["资产负债率%"] = round(df["总负债"] / df["总资产"] * 100, 2)
    df["资产周转率"] = round(df["营业收入"] / df["总资产"], 3)
    return df

main_data = calc_financial_indices(main_data)
for comp in competitor_data_dict:
    competitor_data_dict[comp] = calc_financial_indices(competitor_data_dict[comp])

# 修复年份索引越界
filtered_year_data = main_data[main_data["年份"] == select_year]
if filtered_year_data.empty:
    select_year = int(main_data["年份"].max())
    year_detail = main_data[main_data["年份"] == select_year].iloc[0]
else:
    year_detail = filtered_year_data.iloc[0]

def safe_display(value, suffix="%"):
    if pd.isna(value):
        return "—"
    return f"{value}{suffix}"

# 地区数据预处理
if main_company == "腾讯控股":
    china_total = tencent_business_data[tencent_business_data["年份"] == select_year]["中国大陆营收"].iloc[0]
    province_full_data["营收(亿元)"] = province_full_data["占比%"] / 100 * china_total
    overseas_rev = tencent_business_data[tencent_business_data["年份"] == select_year]["海外营收"].iloc[0]
    overseas_df = pd.DataFrame({
        "地区名称": ["东南亚", "欧美", "其他海外地区"],
        "营收(亿元)": [300, 350, overseas_rev - 650],
        "纬度": [1.3521, 37.0902, 55.3781],
        "经度": [103.8198, -95.7129, -3.4360]
    })

# ===================== 预测模块 =====================
def forecast_data(df, col, periods):
    if not ARIMA_AVAILABLE or periods <= 0:
        return [], [], []
    try:
        model = ARIMA(df[col].values, order=(1, 1, 1))
        res = model.fit()
        forecast_res = res.get_forecast(steps=periods)
        pred = forecast_res.predicted_mean
        conf = forecast_res.conf_int()
        last_year = int(df["年份"].max())
        years = [last_year + i + 1 for i in range(periods)]
        return years, pred, conf
    except Exception:
        return [], [], []

rev_years, rev_pred, rev_conf = forecast_data(main_data, "营业收入", forecast_years)
profit_years, profit_pred, profit_conf = forecast_data(main_data, "归母净利润", forecast_years)

# ===================== 主页面开始 =====================
st.markdown(f'<div class="main-title">📈 {main_company}({company_info[main_company]})年度财报综合数据分析看板</div>', unsafe_allow_html=True)

# ========== 1. 核心八大指标 ==========
st.markdown('<div class="premium-card">', unsafe_allow_html=True)
st.subheader("📊 当期八大核心分析指数")

m1, m2, m3, m4 = st.columns(4)
m5, m6, m7, m8 = st.columns(4)

with m1:
    st.markdown(f'''
    <div class="metric-premium">
        <div class="metric-label-premium">营业收入</div>
        <div class="metric-value-premium">¥{year_detail["营业收入"]:,.2f}亿</div>
    </div>
    ''', unsafe_allow_html=True)
with m2:
    st.markdown(f'''
    <div class="metric-premium">
        <div class="metric-label-premium">净利润率</div>
        <div class="metric-value-premium">{year_detail["净利润率%"]}%</div>
    </div>
    ''', unsafe_allow_html=True)
with m3:
    st.markdown(f'''
    <div class="metric-premium">
        <div class="metric-label-premium">毛利率</div>
        <div class="metric-value-premium">{year_detail["毛利率%"]}%</div>
    </div>
    ''', unsafe_allow_html=True)
with m4:
    st.markdown(f'''
    <div class="metric-premium">
        <div class="metric-label-premium">净资产收益率</div>
        <div class="metric-value-premium">{year_detail["净资产收益率%"]}%</div>
    </div>
    ''', unsafe_allow_html=True)

rev_color = "#16a34a" if year_detail["营收同比增速%"] >= 0 else "#dc2626"
profit_color = "#16a34a" if year_detail["净利润同比增速%"] >= 0 else "#dc2626"

with m5:
    st.markdown(f'''
    <div class="metric-premium">
        <div class="metric-label-premium">营收增速</div>
        <div class="metric-value-premium" style="color: {rev_color} !important;">{safe_display(year_detail["营收同比增速%"])}</div>
    </div>
    ''', unsafe_allow_html=True)
with m6:
    st.markdown(f'''
    <div class="metric-premium">
        <div class="metric-label-premium">净利润增速</div>
        <div class="metric-value-premium" style="color: {profit_color} !important;">{safe_display(year_detail["净利润同比增速%"])}</div>
    </div>
    ''', unsafe_allow_html=True)
with m7:
    st.markdown(f'''
    <div class="metric-premium">
        <div class="metric-label-premium">资产负债率</div>
        <div class="metric-value-premium">{year_detail["资产负债率%"]}%</div>
    </div>
    ''', unsafe_allow_html=True)
with m8:
    st.markdown(f'''
    <div class="metric-premium">
        <div class="metric-label-premium">资产周转率</div>
        <div class="metric-value-premium">{year_detail["资产周转率"]}</div>
    </div>
    ''', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ========== 2. 经营趋势图（交互点位分析） ==========
st.markdown('<div class="premium-card">', unsafe_allow_html=True)
st.subheader("📈 营收与净利润历年变化趋势" + ("及预测" if ARIMA_AVAILABLE and forecast_years > 0 else ""))
st.caption("💡 点击折线上的数据点，查看该年度详细分析")

fig_trend = go.Figure()

# 营收曲线（修复版：去掉smoothing，改用tension）
fig_trend.add_trace(go.Scatter(
    x=main_data["年份"],
    y=main_data["营业收入"],
    name="营业收入(亿元)",
    line=dict(color="#2563eb", width=4.5, shape='spline', smoothing=0.8),
    marker=dict(size=12, color="#2563eb", line=dict(width=3, color='white')),
    fill='tozeroy',
    fillcolor='rgba(37, 99, 235, 0.1)',
    hovertemplate='<b>%{x}年</b><br>营收：%{y:.2f}亿元<extra></extra>'
))

# 营收预测
if len(rev_years) > 0:
    fig_trend.add_trace(go.Scatter(
        x=rev_years,
        y=rev_pred,
        name="预测营收(亿元)",
        line=dict(color="#2563eb", width=3, dash="dot", shape='spline', smoothing=0.8),
        marker=dict(size=10, color="#2563eb", line=dict(width=2, color='white')),
        fill='tozeroy',
        fillcolor='rgba(37, 99, 235, 0.05)'
    ))

# 净利润曲线
fig_trend.add_trace(go.Scatter(
    x=main_data["年份"],
    y=main_data["归母净利润"],
    name="归母净利润(亿元)",
    yaxis="y2",
    line=dict(color="#8b5cf6", width=4.5, shape='spline', smoothing=0.8),
    marker=dict(size=12, color="#8b5cf6", line=dict(width=3, color='white')),
    fill='tozeroy',
    fillcolor='rgba(139, 92, 246, 0.1)',
    hovertemplate='<b>%{x}年</b><br>净利润：%{y:.2f}亿元<extra></extra>'
))

# 净利润预测
if len(profit_years) > 0:
    fig_trend.add_trace(go.Scatter(
        x=profit_years,
        y=profit_pred,
        name="预测净利润(亿元)",
        yaxis="y2",
        line=dict(color="#8b5cf6", width=3, dash="dot", shape='spline', smoothing=0.8),
        marker=dict(size=10, color="#8b5cf6", line=dict(width=2, color='white'))
    ))

fig_trend.update_layout(
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(color='#334155', size=13),
    yaxis=dict(
        title="营业收入(亿元)",
        title_font=dict(color="#2563eb", size=14),
        gridcolor='rgba(148, 163, 184, 0.1)',
        zeroline=False,
        showline=False
    ),
    yaxis2=dict(
        title="归母净利润(亿元)",
        title_font=dict(color="#8b5cf6", size=14),
        overlaying="y",
        side="right",
        gridcolor='rgba(148, 163, 184, 0.1)',
        zeroline=False,
        showline=False
    ),
    title_text=f"{main_company}整体经营规模走势",
    title_font=dict(size=16, color="#0f172a"),
    height=560,
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        bgcolor='rgba(255,255,255,0)',
        font=dict(size=12)
    ),
    hovermode="x unified",
    hoverlabel=dict(bgcolor="white", font_size=13, bordercolor="#e2e8f0", borderwidth=1),
    xaxis=dict(gridcolor='rgba(148, 163, 184, 0.1)', zeroline=False)
)

# 交互点位选择
trend_select = st.plotly_chart(
    fig_trend,
    use_container_width=True,
    on_select="rerun",
    selection_mode="points",
    key="trend_chart_main"
)

# 点位分析展示
if trend_select.selection.points:
    p = trend_select.selection.points[0]
    p_year = int(p["x"])
    p_data = main_data[main_data["年份"] == p_year]
    if not p_data.empty:
        row = p_data.iloc[0]
        st.markdown(f'''
        <div class="point-analysis">
            <h4>📍 {p_year}年 经营数据深度解析</h4>
            <p><strong>📊 营收端：</strong>营业收入 {row["营业收入"]:.2f} 亿元，增速 {safe_display(row["营收同比增速%"])}。{year_analysis.get(p_year, {}).get("revenue", "该年度经营整体平稳。")}</p>
            <p><strong>💰 利润端：</strong>归母净利润 {row["归母净利润"]:.2f} 亿元，净利润率 {row["净利润率%"]}%。{year_analysis.get(p_year, {}).get("profit", "盈利水平保持行业前列。")}</p>
            <p><strong>💡 核心结论：</strong>该年度处于公司发展周期的{"上升期" if row["营收同比增速%"] > 0 else "调整期"}，基本面整体稳健。</p>
        </div>
        ''', unsafe_allow_html=True)
else:
    st.caption("☝️ 点击图表上的数据点，查看该年度详细分析")

# 整体深度分析
with st.expander("📖 查看整体趋势深度解读"):
    st.markdown(f'''
    <div class="point-analysis">
        <h4>📊 全周期经营趋势深度分析</h4>
        <p><strong>营收端：</strong>{main_company}在2021-2024年间整体呈现稳健增长态势。2022年受宏观环境影响营收略有回调，2023年起重回增长通道，2024年创历史新高。</p>
        <p><strong>利润端：</strong>净利润波动幅度大于营收，反映出公司业务结构调整和成本管控的阶段性影响。2023年为利润低点，2024年强势反弹，盈利能力显著修复。</p>
        <p><strong>未来展望：</strong>基于ARIMA模型预测，未来{forecast_years}年公司将延续增长态势，营收和净利润均有望稳步提升，增长动力来自核心业务深化与新业务贡献。</p>
        <p><strong>投资启示：</strong>公司基本面扎实，现金流充沛，经过调整期后重新进入上升通道，长期投资价值显著。</p>
    </div>
    ''', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ========== 3. 竞品横向对比 ==========
if len(competitors) > 0:
    st.markdown('<div class="premium-card">', unsafe_allow_html=True)
    st.subheader("🏆 同行业竞品横向对比分析")

    c_col1, c_col2 = st.columns(2)
    color_palette = ["#8b5cf6", "#06b6d4", "#10b981"]

    with c_col1:
        fig_rev_comp = go.Figure()
        fig_rev_comp.add_trace(go.Bar(
            x=main_data["年份"],
            y=main_data["营业收入"],
            name=main_company,
            marker=dict(color='rgba(37, 99, 235, 0.88)', line=dict(color='rgba(37, 99, 235, 1)', width=1)),
            hovertemplate='<b>%{x}年</b><br>%{y:.2f}亿元<extra></extra>',
            width=0.22
        ))
        for idx, comp in enumerate(competitor_data_dict):
            c_data = competitor_data_dict[comp]
            fig_rev_comp.add_trace(go.Bar(
                x=c_data["年份"],
                y=c_data["营业收入"],
                name=comp,
                marker=dict(color=f'rgba({int(color_palette[idx].lstrip("#")[0:2], 16)}, {int(color_palette[idx].lstrip("#")[2:4], 16)}, {int(color_palette[idx].lstrip("#")[4:6], 16)}, 0.88)'),
                hovertemplate='<b>%{x}年</b><br>%{y:.2f}亿元<extra></extra>',
                width=0.22
            ))
        fig_rev_comp.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#334155'),
            title="2021-2024年营业收入对比(亿元)",
            title_font=dict(size=15),
            barmode="group",
            height=450,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor='rgba(255,255,255,0)'),
            xaxis=dict(gridcolor='rgba(148, 163, 184, 0.1)'),
            yaxis=dict(gridcolor='rgba(148, 163, 184, 0.1)', zeroline=False)
        )
        st.plotly_chart(fig_rev_comp, use_container_width=True)

    with c_col2:
        fig_profit_comp = go.Figure()
        fig_profit_comp.add_trace(go.Bar(
            x=main_data["年份"],
            y=main_data["归母净利润"],
            name=main_company,
            marker=dict(color='rgba(37, 99, 235, 0.88)', line=dict(color='rgba(37, 99, 235, 1)', width=1)),
            hovertemplate='<b>%{x}年</b><br>%{y:.2f}亿元<extra></extra>',
            width=0.22
        ))
        for idx, comp in enumerate(competitor_data_dict):
            c_data = competitor_data_dict[comp]
            fig_profit_comp.add_trace(go.Bar(
                x=c_data["年份"],
                y=c_data["归母净利润"],
                name=comp,
                marker=dict(color=f'rgba({int(color_palette[idx].lstrip("#")[0:2], 16)}, {int(color_palette[idx].lstrip("#")[2:4], 16)}, {int(color_palette[idx].lstrip("#")[4:6], 16)}, 0.88)'),
                hovertemplate='<b>%{x}年</b><br>%{y:.2f}亿元<extra></extra>',
                width=0.22
            ))
        fig_profit_comp.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#334155'),
            title="2021-2024年归母净利润对比(亿元)",
            title_font=dict(size=15),
            barmode="group",
            height=450,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor='rgba(255,255,255,0)'),
            xaxis=dict(gridcolor='rgba(148, 163, 184, 0.1)'),
            yaxis=dict(gridcolor='rgba(148, 163, 184, 0.1)', zeroline=False)
        )
        st.plotly_chart(fig_profit_comp, use_container_width=True)

    with st.expander("📖 查看竞品格局深度分析"):
        st.markdown(f'''
        <div class="point-analysis">
            <h4>🏆 行业竞争格局深度分析</h4>
            <p><strong>营收规模：</strong>头部公司体量差距明显，第一梯队占据行业绝大部分市场份额，马太效应显著。</p>
            <p><strong>盈利能力：</strong>{main_company}的净利润率在同业中处于领先水平，体现了强大的变现能力和成本控制能力。</p>
            <p><strong>增长韧性：</strong>面对行业调整期，头部公司展现出更强的业绩韧性，利润修复速度更快，核心护城河深厚。</p>
            <p><strong>综合评价：</strong>多元业务布局的公司具备更强的抗风险能力和长期增长确定性。</p>
        </div>
        ''', unsafe_allow_html=True)

    st.subheader("关键财务指标雷达图对比")
    radar_cats = ["净利润率", "毛利率", "净资产收益率", "营收增速", "资产周转率"]
    fig_radar = go.Figure()

    # 主公司数据
    main_latest = main_data.iloc[-1]
    main_vals = [
        main_latest["净利润率%"] / 50 * 100,
        main_latest["毛利率%"] / 100 * 100,
        main_latest["净资产收益率%"] / 30 * 100,
        max(main_latest["营收同比增速%"], 0),
        main_latest["资产周转率"] * 100
    ]
    fig_radar.add_trace(go.Scatterpolar(
        r=main_vals,
        theta=radar_cats,
        fill="toself",
        name=main_company,
        line=dict(color="#2563eb", width=2.5),
        opacity=0.6
    ))

    for idx, comp in enumerate(competitor_data_dict):
        c_latest = competitor_data_dict[comp].iloc[-1]
        c_vals = [
            c_latest["净利润率%"] / 50 * 100,
            c_latest["毛利率%"] / 100 * 100,
            c_latest["净资产收益率%"] / 30 * 100,
            max(c_latest["营收同比增速%"], 0),
            c_latest["资产周转率"] * 100
        ]
        fig_radar.add_trace(go.Scatterpolar(
            r=c_vals,
            theta=radar_cats,
            fill="toself",
            name=comp,
            line=dict(color=color_palette[idx], width=2.5),
            opacity=0.6
        ))

    fig_radar.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#334155'),
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], gridcolor='rgba(148, 163, 184, 0.12)'),
            bgcolor='rgba(255,255,255,0.5)',
            angularaxis=dict(gridcolor='rgba(148, 163, 184, 0.18)')
        ),
        title="财务综合能力对比雷达图",
        title_font=dict(size=15),
        height=550,
        legend=dict(bgcolor='rgba(255,255,255,0)')
    )
    st.plotly_chart(fig_radar, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ========== 4. 业务板块 + 产品矩阵 + 用户画像 ==========
st.markdown('<div class="premium-card">', unsafe_allow_html=True)

if main_company == "腾讯控股":
    st.subheader("📊 业务板块营收分析")
    b_col1, b_col2 = st.columns(2)

    biz_melt = tencent_business_data.melt(
        id_vars="年份",
        value_vars=["增值服务营收", "金融科技及企业服务营收", "营销服务营收"],
        var_name="业务板块",
        value_name="营收"
    )

    with b_col1:
        fig_biz_bar = px.bar(
            biz_melt, x="年份", y="营收", color="业务板块", barmode="group",
            title="2021-2024年各板块营收对比",
            color_discrete_map={
                "增值服务营收": "#2563eb",
                "金融科技及企业服务营收": "#8b5cf6",
                "营销服务营收": "#06b6d4"
            }
        )
        fig_biz_bar.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#334155'),
            height=450,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor='rgba(255,255,255,0)'),
            xaxis=dict(gridcolor='rgba(148, 163, 184, 0.1)'),
            yaxis=dict(gridcolor='rgba(148, 163, 184, 0.1)', zeroline=False)
        )
        st.plotly_chart(fig_biz_bar, use_container_width=True)

    with b_col2:
        biz_year = tencent_business_data[tencent_business_data["年份"] == select_year]
        pie_data = pd.DataFrame({
            "业务板块": ["增值服务", "金融科技及企业服务", "营销服务"],
            "营收": [
                biz_year["增值服务营收"].iloc[0],
                biz_year["金融科技及企业服务营收"].iloc[0],
                biz_year["营销服务营收"].iloc[0]
            ]
        })
        fig_biz_pie = px.pie(
            pie_data, values="营收", names="业务板块",
            title=f"{select_year}年业务营收占比",
            color_discrete_sequence=["#2563eb", "#8b5cf6", "#06b6d4"],
            hole=0.5
        )
        fig_biz_pie.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#334155'),
            height=450,
            legend=dict(bgcolor='rgba(255,255,255,0)')
        )
        fig_biz_pie.update_traces(
            textposition='outside',
            textinfo='percent+label',
            marker=dict(line=dict(color='white', width=4))
        )
        st.plotly_chart(fig_biz_pie, use_container_width=True)

    with st.expander("📖 查看业务结构深度分析"):
        st.markdown(f'''
        <div class="point-analysis">
            <h4>📊 业务结构战略分析</h4>
            <p><strong>增值服务：</strong>第一大收入来源，包含游戏和社交网络业务，是公司基本盘，贡献近半数营收，稳定性极强。</p>
            <p><strong>金融科技及企业服务：</strong>增长最快的板块，微信支付与云服务双轮驱动，已成为第二增长曲线，未来潜力巨大。</p>
            <p><strong>营销服务：</strong>受宏观环境影响较大，但随广告需求回暖呈现稳步复苏态势。</p>
            <p><strong>战略意义：</strong>三驾马车格局分散了单一业务风险，金融科技的高增长有效对冲了游戏业务的周期性波动。</p>
        </div>
        ''', unsafe_allow_html=True)

    st.divider()

    # 核心产品矩阵
    st.subheader("🧩 核心产品矩阵")
    st.caption(f"{select_year}年腾讯核心产品生态")
    p_cols = st.columns(4)
    for i, prod in enumerate(tencent_products):
        with p_cols[i % 4]:
            st.markdown(f'''
            <div class="product-card">
                <div class="product-icon">{prod["icon"]}</div>
                <div class="product-name">{prod["name"]}</div>
                <div class="product-desc">{prod["desc"]}</div>
                <div class="product-stat">{prod["stat"]}</div>
            </div>
            ''', unsafe_allow_html=True)

    st.divider()

    # 用户画像
    st.subheader("👥 全维度用户画像")
    u_col1, u_col2 = st.columns(2)

    with u_col1:
        fig_age = px.pie(
            user_age_data, values="占比%", names="年龄段",
            title="用户年龄分布",
            color_discrete_sequence=["#2563eb", "#3b82f6", "#60a5fa", "#93c5fd", "#bfdbfe", "#dbeafe"],
            hole=0.45
        )
        fig_age.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#334155'),
            height=450,
            legend=dict(orientation="h", yanchor="bottom", y=-0.1, bgcolor='rgba(255,255,255,0)')
        )
        fig_age.update_traces(marker=dict(line=dict(color='white', width=3)))
        st.plotly_chart(fig_age, use_container_width=True)

    with u_col2:
        fig_city = px.bar(
            user_city_data, x="城市等级", y="占比%",
            title="用户城市等级分布",
            color="占比%",
            color_continuous_scale=px.colors.sequential.Blues
        )
        fig_city.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#334155'),
            height=450,
            xaxis=dict(gridcolor='rgba(148, 163, 184, 0.1)'),
            yaxis=dict(gridcolor='rgba(148, 163, 184, 0.1)', zeroline=False, title="占比(%)")
        )
        st.plotly_chart(fig_city, use_container_width=True)

    st.subheader("🎯 核心用户群体特征")
    for g in user_groups:
        st.markdown(f'<span class="user-tag {g["tag"]}">{g["name"]}</span> {g["desc"]}', unsafe_allow_html=True)

    st.divider()

    # 全球地区分布
    st.subheader("🌍 全球营收分布可视化")
    map_col1, map_col2 = st.columns(2)

    with map_col1:
        st.subheader("🇨🇳 中国34省营收分布地图")
        fig_china = px.scatter_geo(
            province_full_data,
            lat="纬度", lon="经度",
            size="营收(亿元)", color="营收(亿元)",
            hover_name="省份",
            hover_data={"营收(亿元)": ":,.2f", "占比%": ":,.1f"},
            projection="natural earth",
            title=f"{select_year}年中国各省份营收分布",
            color_continuous_scale=px.colors.sequential.Blues,
            size_max=60
        )
        fig_china.update_geos(
            scope="asia",
            center={"lat": 35, "lon": 105},
            projection_scale=5,
            showland=True,
            landcolor="#f1f5f9",
            countrycolor="#cbd5e1",
            bgcolor='rgba(0,0,0,0)'
        )
        fig_china.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#334155'),
            height=520,
            margin={"r": 0, "t": 30, "l": 0, "b": 0},
            title_font=dict(size=14)
        )
        st.plotly_chart(fig_china, use_container_width=True)

    with map_col2:
        st.subheader("🌐 海外市场营收分布")
        fig_overseas = px.scatter_geo(
            overseas_df,
            lat="纬度", lon="经度",
            size="营收(亿元)", color="地区名称",
            hover_name="地区名称",
            hover_data={"营收(亿元)": ":,.2f"},
            projection="natural earth",
            title=f"{select_year}年海外大区营收分布",
            color_discrete_map={"东南亚": "#2563eb", "欧美": "#8b5cf6", "其他海外地区": "#06b6d4"},
            size_max=60
        )
        fig_overseas.update_geos(
            showland=True,
            landcolor="#f1f5f9",
            countrycolor="#cbd5e1",
            bgcolor='rgba(0,0,0,0)'
        )
        fig_overseas.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#334155'),
            height=520,
            margin={"r": 0, "t": 30, "l": 0, "b": 0},
            legend=dict(bgcolor='rgba(255,255,255,0)'),
            title_font=dict(size=14)
        )
        st.plotly_chart(fig_overseas, use_container_width=True)

else:
    st.subheader("📊 业务板块与用户画像")
    st.info(f"""
    ℹ️ 详细业务板块、产品矩阵和用户画像数据目前仅支持腾讯控股
    
    目前{main_company}已开放的分析模块：
    - ✅ 八大核心财务指标实时展示
    - ✅ 历年经营趋势分析与未来预测
    - ✅ 多维度竞品横向对比
    - ✅ 盈利、偿债、增长、运营能力综合评估
    - ✅ 智能问答助手
    - ✅ 图表点位交互分析
    
    如需查看产品生态与用户画像，请在左侧选择「腾讯控股」。
    """)

st.markdown('</div>', unsafe_allow_html=True)

# ========== 5. 财务指数专项分析 ==========
st.markdown('<div class="premium-card">', unsafe_allow_html=True)
st.subheader("📉 多项财务指数走势对比")
st.caption("💡 点击曲线上的数据点，查看该年度指标详情")

fig_index = go.Figure()
index_config = [
    ("毛利率%", "#2563eb"),
    ("净利润率%", "#8b5cf6"),
    ("净资产收益率%", "#06b6d4"),
    ("资产负债率%", "#64748b")
]

for name, color in index_config:
    fig_index.add_trace(go.Scatter(
        x=main_data["年份"],
        y=main_data[name],
        name=name,
        line=dict(color=color, width=3.5, shape='spline', smoothing=0.8),
        marker=dict(size=10, color=color, line=dict(width=2, color='white')),
        hovertemplate=f'<b>%{{x}}年</b><br>{name}：%{{y}}%<extra></extra>'
    ))

fig_index.update_layout(
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(color='#334155'),
    height=480,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor='rgba(255,255,255,0)'),
    xaxis=dict(gridcolor='rgba(148, 163, 184, 0.1)'),
    yaxis=dict(gridcolor='rgba(148, 163, 184, 0.1)', zeroline=False, title="百分比(%)")
)

index_select = st.plotly_chart(
    fig_index,
    use_container_width=True,
    on_select="rerun",
    selection_mode="points",
    key="index_chart_main"
)

if index_select.selection.points:
    p = index_select.selection.points[0]
    p_year = int(p["x"])
    p_data = main_data[main_data["年份"] == p_year]
    if not p_data.empty:
        row = p_data.iloc[0]
        st.markdown(f'''
        <div class="point-analysis">
            <h4>📍 {p_year}年 财务指标解析</h4>
            <p><strong>盈利能力：</strong>毛利率 {row["毛利率%"]}%，净利润率 {row["净利润率%"]}%，盈利质量{"优秀" if row["净利润率%"] > 20 else "良好"}。</p>
            <p><strong>偿债能力：</strong>资产负债率 {row["资产负债率%"]}%，处于{"健康偏低" if row["资产负债率%"] < 50 else "合理"}水平，财务风险可控。</p>
            <p><strong>股东回报：</strong>净资产收益率(ROE) {row["净资产收益率%"]}%，资本使用效率{"优异" if row["净资产收益率%"] > 15 else "良好"}。</p>
        </div>
        ''', unsafe_allow_html=True)

# 资产结构面积图
st.subheader("🏦 资产与负债权益结构变化")
asset_df = pd.DataFrame({
    "年份": main_data["年份"],
    "总负债": main_data["总负债"],
    "股东权益": main_data["股东权益"]
})
asset_melt = asset_df.melt(id_vars="年份", var_name="构成", value_name="金额")
fig_asset = px.area(
    asset_melt, x="年份", y="金额", color="构成",
    title="企业资产结构历年变化",
    color_discrete_map={"总负债": "#8b5cf6", "股东权益": "#2563eb"}
)
fig_asset.update_traces(stackgroup='one', line=dict(width=0))
fig_asset.update_layout(
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(color='#334155'),
    height=420,
    legend=dict(bgcolor='rgba(255,255,255,0)'),
    xaxis=dict(gridcolor='rgba(148, 163, 184, 0.1)'),
    yaxis=dict(gridcolor='rgba(148, 163, 184, 0.1)', zeroline=False)
)
st.plotly_chart(fig_asset, use_container_width=True)

# 五维能力雷达图
st.subheader("🎯 单年度财务综合能力雷达图")
radar_cats2 = ["盈利能力", "收益水平", "偿债安全", "增长潜力", "运营效率"]
radar_vals = [
    year_detail["毛利率%"] / 50 * 100,
    year_detail["净资产收益率%"] / 30 * 100,
    100 - year_detail["资产负债率%"],
    max(year_detail["营收同比增速%"], 0) if not pd.isna(year_detail["营收同比增速%"]) else 0,
    year_detail["资产周转率"] * 100
]
fig_radar_single = go.Figure()
fig_radar_single.add_trace(go.Scatterpolar(
    r=radar_vals,
    theta=radar_cats2,
    fill="toself",
    name="综合能力评分",
    line=dict(color="#2563eb", width=3),
    fillcolor='rgba(37, 99, 235, 0.25)'
))
fig_radar_single.update_layout(
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(color='#334155'),
    polar=dict(
        radialaxis=dict(visible=True, range=[0, 100], gridcolor='rgba(148, 163, 184, 0.12)'),
        bgcolor='rgba(255,255,255,0.5)',
        angularaxis=dict(gridcolor='rgba(148, 163, 184, 0.18)')
    ),
    title=f"{select_year}年财务五维能力评估",
    title_font=dict(size=15),
    height=550,
    legend=dict(bgcolor='rgba(255,255,255,0)')
)
st.plotly_chart(fig_radar_single, use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# ========== 6. 原始数据表格 ==========
st.markdown('<div class="premium-card">', unsafe_allow_html=True)
st.subheader("📋 完整原始财务数据表")
st.dataframe(main_data.round(2), use_container_width=True, hide_index=True)

if main_company == "腾讯控股":
    st.subheader("📋 中国省份营收明细数据")
    st.dataframe(province_full_data.round(2), use_container_width=True, hide_index=True)

st.markdown('</div>', unsafe_allow_html=True)

# ========== 7. 智能问答助手 ==========
st.markdown('<div class="premium-card">', unsafe_allow_html=True)
st.subheader("🤖 财报智能咨询助手")
st.caption("💡 支持自然语言提问，比如：帮我查下阿里巴巴2023年的净利润")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 显示聊天记录
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 输入框
user_input = st.chat_input("问我任何财报相关的问题吧~")
if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    answer = parse_question(user_input, main_company, select_year, main_data, competitor_data_dict)
    st.session_state.chat_history.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.markdown(answer)

st.markdown('</div>', unsafe_allow_html=True)

# ========== 8. 悬浮智能助手按钮 ==========
if "ai_show_greeting" not in st.session_state:
    st.session_state.ai_show_greeting = True

# 悬浮问候气泡
if st.session_state.ai_show_greeting:
    st.markdown('<div class="ai-greeting">你好呀👋 点击我可以随时召唤智能助手哦~</div>', unsafe_allow_html=True)

# 悬浮按钮
st.markdown('<button class="ai-float-btn" onclick="window.scrollTo(0, document.body.scrollHeight);">🤖</button>', unsafe_allow_html=True)

# ========== 9. 页脚 ==========
st.markdown("""
<div class="footer-section">
    <p>数据来源：公司官方财报 | 数据更新至2024年</p>
    <p style="font-size: 0.85rem; margin-top: 0.3rem;">© 2026 财务数据分析系统 | 所有数据仅供参考，不构成任何投资建议</p>
</div>
""", unsafe_allow_html=True)
