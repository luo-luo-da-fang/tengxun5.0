import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
from io import BytesIO
import re
import warnings
warnings.filterwarnings('ignore')

# ========== 可选依赖导入（缺库不崩溃） ==========
try:
    import qrcode
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False

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

# ========== 全局配置 ==========
company_info = {
    "腾讯控股": "00700.HK",
    "阿里巴巴": "9988.HK",
    "百度": "BIDU",
    "网易": "NTES"
}
all_company_list = ["腾讯控股", "阿里巴巴", "百度", "网易"]

st.set_page_config(
    page_title="年度财报综合分析看板",
    layout="wide",
    page_icon="📈",
    initial_sidebar_state="expanded"
)

# ========== 全局样式 ==========
st.markdown("""
<style>
.stApp {
    background: linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%);
    font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
    color: #0f172a;
}
.main-title {
    font-size: 2.2rem !important;
    font-weight: 700 !important;
    text-align: center;
    padding: 2rem 0 1.5rem 0;
    background: linear-gradient(135deg, #1e40af 0%, #6366f1 50%, #8b5cf6 100%);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: 2px;
    position: relative;
    margin-bottom: 2rem;
}
.main-title::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 120px;
    height: 3px;
    background: linear-gradient(90deg, transparent, #6366f1, transparent);
    border-radius: 2px;
}
.premium-card {
    background: #ffffff;
    border-radius: 16px;
    padding: 1.8rem;
    margin-bottom: 2rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05),
                0 20px 25px -5px rgba(0, 0, 0, 0.05);
    border: 1px solid rgba(148, 163, 184, 0.1);
    transition: all 0.35s ease;
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
    background: linear-gradient(90deg, #3b82f6, #8b5cf6, #ec4899);
}
.premium-card:hover {
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08),
                0 25px 50px -12px rgba(0, 0, 0, 0.08);
    transform: translateY(-2px);
}
.metric-premium {
    background: linear-gradient(145deg, #f8fafc 0%, #eef2ff 100%);
    border-radius: 12px;
    padding: 1.3rem 1rem;
    text-align: center;
    border: 1px solid rgba(99, 102, 241, 0.15);
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}
.metric-premium::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #3b82f6, #8b5cf6);
    transform: scaleX(0);
    transition: transform 0.3s ease;
}
.metric-premium:hover::after { transform: scaleX(1); }
.metric-premium:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 25px -5px rgba(99, 102, 241, 0.2);
}
.metric-value-premium {
    font-size: 1.75rem !important;
    font-weight: 700 !important;
    background: linear-gradient(135deg, #1e40af, #6366f1);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0.5rem 0;
    font-family: 'DIN Alternate', sans-serif;
}
.metric-label-premium {
    font-size: 0.9rem !important;
    color: #64748b !important;
    font-weight: 500;
    letter-spacing: 0.5px;
}
.css-1d391kg {
    background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
    border-right: 1px solid rgba(148, 163, 184, 0.15);
}
.analysis-box {
    background: linear-gradient(135deg, #eff6ff 0%, #e0e7ff 100%);
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    margin-top: 1rem;
    border-left: 4px solid #6366f1;
}
.analysis-box h4 {
    color: #3730a3;
    margin-bottom: 0.8rem;
    font-size: 1rem;
}
.analysis-box p {
    color: #1e293b;
    line-height: 1.8;
    margin-bottom: 0.5rem;
}
.ai-avatar {
    width: 50px;
    height: 50px;
    border-radius: 50%;
    background: linear-gradient(135deg, #6366f1, #8b5cf6, #ec4899);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
    animation: float 3s ease-in-out infinite;
}
@keyframes float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-5px); }
}
.stChatMessage {
    background: white;
    border-radius: 12px;
    border: 1px solid rgba(148, 163, 184, 0.1);
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}
.stChatMessage[data-testid="user-message"] {
    background: linear-gradient(135deg, #eff6ff 0%, #e0e7ff 100%);
    border-color: rgba(99, 102, 241, 0.2);
}
.footer-section {
    text-align: center;
    color: #64748b;
    padding: 2rem 1rem;
    border-top: 1px solid rgba(148, 163, 184, 0.15);
    margin-top: 3rem;
    font-size: 0.85rem;
}
.stButton > button {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 0.55rem 1.4rem;
    font-weight: 600;
    transition: all 0.3s ease;
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.25);
}
.stButton > button:hover {
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(99, 102, 241, 0.35);
}
.stRadio > div > label[data-checked="true"] {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    color: white;
    border-color: #6366f1;
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.25);
}
</style>
""", unsafe_allow_html=True)

# ========== 智能问答解析模块 ==========
def parse_user_query(query):
    query = query.lower()
    target_company = None
    for comp in all_company_list:
        if comp.lower() in query or comp[:2].lower() in query:
            target_company = comp
            break
    year_match = re.search(r'(20\d{2})年?', query)
    target_year = int(year_match.group(1)) if year_match else None
    indicators = {
        "营收": ["营收", "收入", "营业额", "销售额"],
        "净利润": ["净利润", "利润", "盈利", "赚了"],
        "毛利率": ["毛利率", "毛利"],
        "负债率": ["负债", "负债率", "资产负债"],
        "增速": ["增速", "增长", "涨了", "涨幅"],
        "ROE": ["净资产收益率", "roe", "股东回报"]
    }
    target_ind = None
    for ind, keywords in indicators.items():
        for kw in keywords:
            if kw in query:
                target_ind = ind
                break
        if target_ind:
            break
    greetings = ["你好", "您好", "hi", "hello", "嗨", "在吗", "在不在"]
    is_greeting = any(g in query for g in greetings)
    return {
        "company": target_company,
        "year": target_year,
        "indicator": target_ind,
        "is_greeting": is_greeting
    }

def generate_answer(parsed, main_comp, year, data_dict):
    comp = parsed["company"] if parsed["company"] else main_comp
    y = parsed["year"] if parsed["year"] else year
    if parsed["is_greeting"] and not parsed["indicator"]:
        return "你好呀😊 我是财报小助手~ 你可以问我任何关于腾讯、阿里、百度、网易的财报问题，比如「阿里巴巴2024年营收多少」「腾讯净利润怎么样」，我都会为你解答哦！"
    if comp not in data_dict:
        return f"抱歉，暂时没有{comp}的详细数据哦~ 你可以查询腾讯控股、阿里巴巴、百度、网易这四家公司的财报信息。"
    df = data_dict[comp]
    year_data = df[df["年份"] == y]
    if year_data.empty:
        year_data = df.iloc[-1]
        y = int(df["年份"].max())
    else:
        year_data = year_data.iloc[0]
    ind = parsed["indicator"]
    if ind == "营收":
        growth = year_data["营收同比增速%"]
        growth_text = f"同比增长{growth}%" if growth > 0 else f"同比下降{abs(growth)}%" if growth < 0 else "与上年持平"
        return f"📊 {comp}在{y}年的营业收入为 **{year_data['营业收入']:.2f}亿元**，{growth_text}。整体经营规模保持稳健发展态势。"
    elif ind == "净利润":
        growth = year_data["净利润同比增速%"]
        growth_text = f"同比增长{growth}%" if growth > 0 else f"同比下降{abs(growth)}%" if growth < 0 else "与上年持平"
        return f"💰 {comp}在{y}年的归母净利润为 **{year_data['归母净利润']:.2f}亿元**，净利润率达到{year_data['净利润率%']}%，{growth_text}。盈利能力表现{'优秀' if year_data['净利润率%'] > 20 else '良好'}。"
    elif ind == "毛利率":
        return f"📈 {comp}在{y}年的毛利率为 **{year_data['毛利率%']}%**，处于行业{'较高' if year_data['毛利率%'] > 50 else '中等'}水平，体现了公司较强的定价能力和成本控制水平。"
    elif ind == "负债率":
        level = "健康安全" if year_data["资产负债率%"] < 50 else "适中" if year_data["资产负债率%"] < 70 else "偏高"
        return f"🏦 {comp}在{y}年的资产负债率为 **{year_data['资产负债率%']}%**，财务结构{level}，偿债风险{'较低' if year_data['资产负债率%'] < 50 else '可控'}。"
    elif ind == "增速":
        return f"🚀 {comp}在{y}年：营收增速为{year_data['营收同比增速%']}%，净利润增速为{year_data['净利润同比增速%']}%，{'增长势头良好' if year_data['营收同比增速%'] > 0 else '处于调整期'}。"
    elif ind == "ROE":
        return f"💎 {comp}在{y}年的净资产收益率(ROE)为 **{year_data['净资产收益率%']}%**，为股东创造回报的能力{'很强' if year_data['净资产收益率%'] > 15 else '良好'}。"
    else:
        return f"""
        📋 **{comp} {y}年财报概览**：
        - 营业收入：{year_data['营业收入']:.2f}亿元
        - 归母净利润：{year_data['归母净利润']:.2f}亿元
        - 净利润率：{year_data['净利润率%']}%
        - 毛利率：{year_data['毛利率%']}%
        - 资产负债率：{year_data['资产负债率%']}%
        
        你可以继续问我具体指标哦~ 比如「毛利率多少」「负债情况怎么样」
        """

# ========== 数据源模块 ==========
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
        for year_idx in range(min(years, len(income_stmt.columns))):
            date = income_stmt.columns[year_idx]
            year_num = date.year
            revenue = income_stmt.loc['Total Revenue', date] if 'Total Revenue' in income_stmt.index else np.nan
            cost = income_stmt.loc['Cost Of Revenue', date] if 'Cost Of Revenue' in income_stmt.index else np.nan
            net_income = income_stmt.loc['Net Income', date] if 'Net Income' in income_stmt.index else np.nan
            total_assets = balance_sheet.loc['Total Assets', date] if 'Total Assets' in balance_sheet.index else np.nan
            total_liab = balance_sheet.loc['Total Liabilities Net Minority Interest', date] if 'Total Liabilities Net Minority Interest' in balance_sheet.index else np.nan
            equity = balance_sheet.loc['Stockholders Equity', date] if 'Stockholders Equity' in balance_sheet.index else np.nan
            op_cash = cashflow.loc['Operating Cash Flow', date] if 'Operating Cash Flow' in cashflow.index else np.nan
            rate = 0.00000001
            if ticker == 'BIDU':
                rate *= 7
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
        return df.sort_values("年份").reset_index(drop=True)
    except Exception:
        return None

# 本地备份数据
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

# 腾讯专属业务数据
tencent_business_data = pd.DataFrame({
    "年份": [2021, 2022, 2023, 2024],
    "增值服务营收": [2916.71, 2875.59, 2876.44, 3252.08],
    "金融科技及企业服务营收": [1722.00, 1771.52, 2170.39, 2378.52],
    "营销服务营收": [886.69, 827.75, 958.62, 1015.26],
    "中国大陆营收": [4929.04, 4879.10, 5361.33, 5815.36],
    "海外营收": [672.14, 666.42, 728.82, 787.21],
})

# 通用数据点解读
general_point_analysis = {
    2021: "2021年行业整体处于上升期，互联网公司普遍取得较好业绩。",
    2022: "2022年受宏观环境与行业监管影响，多数公司业绩承压。",
    2023: "2023年行业进入调整修复期，公司普遍进行成本优化。",
    2024: "2024年行业全面复苏，降本增效成效显现，业绩回暖明显。"
}

# 腾讯专属深度解读
tencent_point_analysis = {
    2021: "2021年受益于游戏、社交广告等业务高速增长，腾讯营收达到阶段性高点。",
    2022: "2022年受宏观经济及行业监管影响，广告和游戏业务承压，营收小幅回调。",
    2023: "2023年金融科技及企业服务业务发力，带动整体营收重回增长轨道。",
    2024: "2024年各项业务全面复苏，增值服务回暖，金融科技持续高增，营收创历史新高。"
}

# ========== 侧边控制面板 ==========
with st.sidebar:
    st.header("🎛️ 财报分析控制台")
    data_source_options = ["本地备份数据"]
    if YFINANCE_AVAILABLE:
        data_source_options.insert(0, "自动获取(推荐)")
    data_source = st.radio(
        "数据来源",
        data_source_options,
        help="自动获取失败时将自动回退到本地备份数据"
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
        forecast_years = st.slider("预测未来年数", 1, 5, 3)
    else:
        st.info("预测功能需要安装statsmodels库")
        forecast_years = 0
    st.divider()
    st.info("💡 数据已预加载至2024年")

# ========== 数据加载与处理 ==========
@st.cache_data
def load_company_data(company_name, use_api):
    if use_api and YFINANCE_AVAILABLE:
        data = fetch_financial_data(company_info[company_name])
        if data is not None and len(data) >= 3:
            return data
    return backup_data[company_name].copy()

use_api = (data_source == "自动获取(推荐)")
all_data_dict = {}
for comp in [main_company] + competitors:
    all_data_dict[comp] = load_company_data(comp, use_api)

def calculate_indices(df):
    df = df.copy()
    df["毛利率%"] = round((df["营业收入"] - df["营业成本"]) / df["营业收入"] * 100, 2)
    df["净利润率%"] = round(df["归母净利润"] / df["营业收入"] * 100, 2)
    df["净资产收益率%"] = round(df["归母净利润"] / df["股东权益"] * 100, 2)
    df["营收同比增速%"] = round(df["营业收入"].pct_change() * 100, 2)
    df["净利润同比增速%"] = round(df["归母净利润"].pct_change() * 100, 2)
    df["资产负债率%"] = round(df["总负债"] / df["总资产"] * 100, 2)
    df["资产周转率"] = round(df["营业收入"] / df["总资产"], 3)
    return df

for comp in all_data_dict:
    all_data_dict[comp] = calculate_indices(all_data_dict[comp])

main_data = all_data_dict[main_company]

# 年份容错
filtered = main_data[main_data["年份"] == select_year]
if filtered.empty:
    select_year = int(main_data["年份"].max())
    year_detail = main_data.iloc[-1]
else:
    year_detail = filtered.iloc[0]

def safe_display(value, suffix="%"):
    if pd.isna(value):
        return "—"
    return f"{value}{suffix}"

# 省份数据（仅腾讯）
province_full_data = pd.DataFrame({
    "省份": ["北京市","天津市","河北省","山西省","内蒙古自治区","辽宁省","吉林省","黑龙江省","上海市","江苏省","浙江省","安徽省","福建省","江西省","山东省","河南省","湖北省","湖南省","广东省","广西壮族自治区","海南省","重庆市","四川省","贵州省","云南省","西藏自治区","陕西省","甘肃省","青海省","宁夏回族自治区","新疆维吾尔自治区","香港特别行政区","澳门特别行政区","台湾省"],
    "纬度": [39.9042,39.0842,38.0428,37.8706,40.8263,41.8045,43.8868,45.7366,31.2304,32.0603,30.2741,31.8612,26.0745,28.6756,36.6758,34.7466,30.5928,28.2282,23.1291,22.8152,20.0440,29.4316,30.6572,26.6470,25.0406,29.6456,34.2648,36.0611,36.6235,38.4872,43.8256,22.3193,22.1987,23.6978],
    "经度": [116.4074,117.2009,114.5149,112.5489,111.7659,123.4327,125.3245,126.6617,121.4737,118.7626,120.1551,117.2830,119.3062,115.8921,117.0009,113.6254,114.3055,112.9388,113.2644,108.3275,110.1987,106.9123,104.0658,106.6342,102.7123,91.1175,108.9542,103.8343,101.7782,106.2309,87.6168,114.1694,113.5439,120.9605],
    "占比%": [7.8,2.1,4.5,1.8,1.2,2.5,1.1,1.0,8.3,14.8,12.7,2.3,4.3,1.9,9.3,5.2,4.8,3.1,21.2,1.7,0.8,2.4,6.3,1.0,1.5,0.1,2.9,0.7,0.2,0.3,0.9,3.5,0.5,2.0]
})

if main_company == "腾讯控股":
    china_total = tencent_business_data[tencent_business_data["年份"] == select_year]["中国大陆营收"].iloc[0]
    province_full_data["营收(亿元)"] = province_full_data["占比%"] / 100 * china_total
    overseas_revenue = tencent_business_data[tencent_business_data["年份"] == select_year]["海外营收"].iloc[0]
    overseas_data = pd.DataFrame({
        "地区名称": ["东南亚", "欧美", "其他海外地区"],
        "营收(亿元)": [300, 350, overseas_revenue - 650],
        "纬度": [1.3521, 37.0902, 55.3781],
        "经度": [103.8198, -95.7129, -3.4360]
    })

# 预测模块
def predict_data(df, col, periods):
    if not ARIMA_AVAILABLE or periods <= 0:
        return [], [], []
    try:
        model = ARIMA(df[col].values, order=(1,1,1))
        res = model.fit()
        fc = res.get_forecast(steps=periods)
        years = [int(df["年份"].max()) + i + 1 for i in range(periods)]
        return years, fc.predicted_mean, fc.conf_int()
    except Exception:
        return [], [], []

rev_years, rev_pred, rev_ci = predict_data(main_data, "营业收入", forecast_years)
profit_years, profit_pred, profit_ci = predict_data(main_data, "归母净利润", forecast_years)

# 动态主标题
st.markdown(f'<div class="main-title">📈 {main_company}({company_info[main_company]})年度财报综合数据分析看板</div>', unsafe_allow_html=True)

# ========== 核心指标卡片 ==========
st.markdown('<div class="premium-card">', unsafe_allow_html=True)
st.subheader("📊 当期八大核心分析指数")
c1,c2,c3,c4 = st.columns(4)
c5,c6,c7,c8 = st.columns(4)

metrics = [
    ("营业收入", f"¥{year_detail['营业收入']:,.2f}亿"),
    ("净利润率", f"{year_detail['净利润率%']}%"),
    ("毛利率", f"{year_detail['毛利率%']}%"),
    ("净资产收益率", f"{year_detail['净资产收益率%']}%"),
    ("营收增速", safe_display(year_detail["营收同比增速%"]), year_detail["营收同比增速%"] >= 0),
    ("净利润增速", safe_display(year_detail["净利润同比增速%"]), year_detail["净利润同比增速%"] >= 0),
    ("资产负债率", f"{year_detail['资产负债率%']}%"),
    ("资产周转率", f"{year_detail['资产周转率']}")
]

cols = [c1,c2,c3,c4,c5,c6,c7,c8]
for i, item in enumerate(metrics):
    label, val = item[0], item[1]
    if len(item) == 3:
        is_positive = item[2]
        color = "#16a34a" if is_positive else "#dc2626"
        style = f"color: {color} !important;"
    else:
        style = ""
    cols[i].markdown(f'''
    <div class="metric-premium">
        <div class="metric-label-premium">{label}</div>
        <div class="metric-value-premium" style="{style}">{val}</div>
    </div>
    ''', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ========== 经营趋势图 ==========
st.markdown('<div class="premium-card">', unsafe_allow_html=True)
st.subheader("📈 营收与净利润历年变化趋势" + ("及预测" if ARIMA_AVAILABLE and forecast_years > 0 else ""))

# 渐变趋势图
fig_trend = go.Figure()
fig_trend.add_trace(go.Scatter(
    x=main_data["年份"], y=main_data["营业收入"],
    name="营业收入(亿元)",
    line=dict(color="#6366f1", width=3.5),
    fill='tozeroy',
    fillcolor='rgba(99, 102, 241, 0.12)',
    marker=dict(size=9, color="#6366f1"),
    hovertemplate='%{y:.2f}亿元<extra></extra>'
))
if len(rev_years) > 0:
    fig_trend.add_trace(go.Scatter(
        x=rev_years, y=rev_pred,
        name="预测营收(亿元)",
        line=dict(color="#6366f1", width=3, dash="dash"),
        fillcolor='rgba(99, 102, 241, 0.08)',
        fill='tonexty'
    ))
fig_trend.add_trace(go.Scatter(
    x=main_data["年份"], y=main_data["归母净利润"],
    name="归母净利润(亿元)",
    yaxis="y2",
    line=dict(color="#ec4899", width=3.5),
    fill='tozeroy',
    fillcolor='rgba(236, 72, 153, 0.12)',
    marker=dict(size=9, color="#ec4899"),
    hovertemplate='%{y:.2f}亿元<extra></extra>'
))
if len(profit_years) > 0:
    fig_trend.add_trace(go.Scatter(
        x=profit_years, y=profit_pred,
        name="预测净利润(亿元)",
        yaxis="y2",
        line=dict(color="#ec4899", width=3, dash="dash"),
        fillcolor='rgba(236, 72, 153, 0.08)',
        fill='tonexty'
    ))

fig_trend.update_layout(
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(color='#334155', size=13),
    yaxis=dict(
        title="营业收入(亿元)",
        title_font=dict(color="#6366f1"),
        gridcolor='rgba(148,163,184,0.12)',
        zeroline=False
    ),
    yaxis2=dict(
        title="归母净利润(亿元)",
        title_font=dict(color="#ec4899"),
        overlaying="y",
        side="right",
        gridcolor='rgba(148,163,184,0.12)',
        zeroline=False
    ),
    height=500,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor='rgba(255,255,255,0)'),
    hovermode="x unified",
    hoverlabel=dict(bgcolor="white", bordercolor="#e2e8f0")
)

# 显示图表 + 放大展开
col_chart, col_btn = st.columns([10, 1])
with col_chart:
    selected_event = st.plotly_chart(
        fig_trend,
        use_container_width=True,
        on_select="rerun",
        selection_mode="points",
        key="trend_chart"
    )
with col_btn:
    show_large = st.button("🔍 放大", key="btn_large")

# 点击数据点解读（完整容错）
try:
    if selected_event and hasattr(selected_event, 'selection') and selected_event.selection and selected_event.selection.points:
        point = selected_event.selection.points[0]
        point_year = int(point["x"])
        point_value = round(point["y"], 2)
        
        analysis = tencent_point_analysis if main_company == "腾讯控股" else general_point_analysis
        analysis_text = analysis.get(point_year, "该年份数据反映了当时的行业环境与公司经营状况。")
        
        st.markdown(f'''
        <div class="analysis-box">
            <h4>📍 {point_year}年数据点深度解读</h4>
            <p>该数据点数值为 <strong>{point_value}亿元</strong></p>
            <p>{analysis_text}</p>
        </div>
        ''', unsafe_allow_html=True)
except Exception:
    pass

# 放大视图
if show_large:
    with st.expander("📐 大图详细视图", expanded=True):
        st.plotly_chart(fig_trend, use_container_width=True, height=700)
        st.markdown("### 💡 各年份数据说明")
        analysis = tencent_point_analysis if main_company == "腾讯控股" else general_point_analysis
        for y in sorted(analysis.keys()):
            st.markdown(f"- **{y}年**：{analysis[y]}")

# 深度分析
with st.expander("💡 查看完整深度分析"):
    st.markdown(f'''
    <div class="analysis-box">
        <h4>📊 经营趋势深度分析</h4>
        <p><strong>营收端：</strong>{main_company}在2021-2024年间整体呈现稳健增长态势。2022年受宏观环境影响营收略有回调，2023年起重回增长通道，2024年创历史新高。</p>
        <p><strong>利润端：</strong>净利润波动幅度大于营收，反映出公司业务结构调整和成本管控的阶段性影响。2023年为利润低点，2024年强势反弹，盈利能力显著修复。</p>
        <p><strong>未来展望：</strong>基于ARIMA模型预测，未来{forecast_years}年公司将延续增长态势，营收和净利润均有望稳步提升。</p>
    </div>
    ''', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ========== 竞品对比（彻底修复 gradientcolor 报错） ==========
if len(competitors) > 0:
    st.markdown('<div class="premium-card">', unsafe_allow_html=True)
    st.subheader("🏆 同行业竞品横向对比分析")
    col1, col2 = st.columns(2)
    
    # 紫蓝渐变色阶（官方标准写法）
    purple_gradient = [[0, "#a78bfa"], [1, "#4f46e5"]]
    comp_colors = ["#ec4899", "#06b6d4", "#10b981"]
    # 生成渐变数值数组
    gradient_vals = [0.2, 0.5, 0.8, 1.0]
    
    with col1:
        fig_rev = go.Figure()
        # 主公司：使用数值数组 + colorscale 实现柱状渐变
        fig_rev.add_trace(go.Bar(
            x=main_data["年份"], y=main_data["营业收入"],
            name=main_company,
            marker=dict(
                color=gradient_vals,
                colorscale=purple_gradient,
                showscale=False
            ),
            hovertemplate='%{y:.2f}亿元<extra></extra>'
        ))
        # 竞品公司：纯色区分
        for i, comp in enumerate(competitors):
            fig_rev.add_trace(go.Bar(
                x=all_data_dict[comp]["年份"], y=all_data_dict[comp]["营业收入"],
                name=comp,
                marker_color=comp_colors[i],
                hovertemplate='%{y:.2f}亿元<extra></extra>'
            ))
        fig_rev.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#334155'),
            title="营业收入对比(亿元)",
            barmode="group",
            height=420,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(gridcolor='rgba(148,163,184,0.12)'),
            yaxis=dict(gridcolor='rgba(148,163,184,0.12)', zeroline=False)
        )
        st.plotly_chart(fig_rev, use_container_width=True)
    
    with col2:
        fig_profit = go.Figure()
        fig_profit.add_trace(go.Bar(
            x=main_data["年份"], y=main_data["归母净利润"],
            name=main_company,
            marker=dict(
                color=gradient_vals,
                colorscale=purple_gradient,
                showscale=False
            ),
            hovertemplate='%{y:.2f}亿元<extra></extra>'
        ))
        for i, comp in enumerate(competitors):
            fig_profit.add_trace(go.Bar(
                x=all_data_dict[comp]["年份"], y=all_data_dict[comp]["归母净利润"],
                name=comp,
                marker_color=comp_colors[i],
                hovertemplate='%{y:.2f}亿元<extra></extra>'
            ))
        fig_profit.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#334155'),
            title="归母净利润对比(亿元)",
            barmode="group",
            height=420,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(gridcolor='rgba(148,163,184,0.12)'),
            yaxis=dict(gridcolor='rgba(148,163,184,0.12)', zeroline=False)
        )
        st.plotly_chart(fig_profit, use_container_width=True)

    with st.expander("💡 查看竞品深度分析"):
        st.markdown(f'''
        <div class="analysis-box">
            <h4>🏆 行业竞争格局分析</h4>
            <p><strong>营收规模：</strong>头部公司体量差距明显，第一梯队占据行业绝大部分市场份额。</p>
            <p><strong>盈利能力：</strong>{main_company}净利润率处于行业领先水平，变现能力和成本控制能力突出。</p>
            <p><strong>增长韧性：</strong>面对行业调整期，头部公司展现出更强的业绩韧性和利润修复能力。</p>
        </div>
        ''', unsafe_allow_html=True)
    
    # 雷达图
    comp_df = []
    for comp in [main_company] + competitors:
        d = all_data_dict[comp].iloc[-1]
        comp_df.append({
            "公司": comp,
            "净利润率(%)": d["净利润率%"],
            "毛利率(%)": d["毛利率%"],
            "净资产收益率(%)": d["净资产收益率%"],
            "营收增速(%)": max(d["营收同比增速%"], 0) if not pd.isna(d["营收同比增速%"]) else 0,
            "资产周转率": d["资产周转率"] * 100
        })
    comp_df = pd.DataFrame(comp_df)
    
    fig_radar = go.Figure()
    cats = ["净利润率(%)", "毛利率(%)", "净资产收益率(%)", "营收增速(%)", "资产周转率"]
    for i, row in comp_df.iterrows():
        fig_radar.add_trace(go.Scatterpolar(
            r=[row[c] for c in cats], theta=cats, fill="toself",
            name=row["公司"],
            line=dict(color="#6366f1" if i==0 else comp_colors[i-1], width=2),
            opacity=0.7
        ))
    fig_radar.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#334155'),
        polar=dict(radialaxis=dict(visible=True, range=[0,100], gridcolor='rgba(148,163,184,0.12)'), bgcolor='rgba(255,255,255,0.5)'),
        title="财务综合能力对比雷达图",
        height=500
    )
    st.plotly_chart(fig_radar, use_container_width=True)
    st.dataframe(comp_df.round(2), use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ========== 业务板块与地区分布 ==========
st.markdown('<div class="premium-card">', unsafe_allow_html=True)

if main_company == "腾讯控股":
    st.subheader("📊 各业务板块营收分析")
    c1, c2 = st.columns(2)
    
    biz_trend = tencent_business_data.melt(
        id_vars="年份",
        value_vars=["增值服务营收","金融科技及企业服务营收","营销服务营收"],
        var_name="业务板块", value_name="营收"
    )
    with c1:
        fig_biz_bar = px.bar(biz_trend, x="年份", y="营收", color="业务板块", barmode="group",
                             title="板块营收对比",
                             color_discrete_map={"增值服务营收":"#6366f1","金融科技及企业服务营收":"#ec4899","营销服务营收":"#06b6d4"})
        fig_biz_bar.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#334155'),
            height=420,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(gridcolor='rgba(148,163,184,0.12)'),
            yaxis=dict(gridcolor='rgba(148,163,184,0.12)', zeroline=False)
        )
        st.plotly_chart(fig_biz_bar, use_container_width=True)
    
    biz_now = pd.DataFrame({
        "业务板块": ["增值服务", "金融科技及企业服务", "营销服务"],
        "营收": [
            tencent_business_data[tencent_business_data["年份"]==select_year]["增值服务营收"].iloc[0],
            tencent_business_data[tencent_business_data["年份"]==select_year]["金融科技及企业服务营收"].iloc[0],
            tencent_business_data[tencent_business_data["年份"]==select_year]["营销服务营收"].iloc[0]
        ]
    })
    with c2:
        fig_biz_pie = px.pie(biz_now, values="营收", names="业务板块",
                            title=f"{select_year}年业务营收占比",
                            color_discrete_sequence=["#6366f1", "#ec4899", "#06b6d4"],
                            hole=0.45)
        fig_biz_pie.update_traces(textposition='outside', textinfo='percent+label')
        fig_biz_pie.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#334155'),
            height=420
        )
        st.plotly_chart(fig_biz_pie, use_container_width=True)

    with st.expander("💡 查看业务板块深度分析"):
        st.markdown('''
        <div class="analysis-box">
            <h4>📊 业务结构分析</h4>
            <p><strong>增值服务：</strong>第一大收入来源，包含游戏和社交网络，是公司基本盘，稳定性强。</p>
            <p><strong>金融科技及企业服务：</strong>增长最快的板块，微信支付+云服务双轮驱动，第二增长曲线。</p>
            <p><strong>营销服务：</strong>受宏观环境影响较大，随广告需求回暖稳步复苏。</p>
        </div>
        ''', unsafe_allow_html=True)
    
    st.divider()
    st.subheader("🌍 全球营收分布")
    m1, m2 = st.columns(2)
    
    with m1:
        fig_map1 = px.scatter_geo(
            province_full_data, lat="纬度", lon="经度", size="营收(亿元)", color="营收(亿元)",
            hover_name="省份", projection="natural earth",
            title="中国全省份营收分布",
            color_continuous_scale=px.colors.sequential.Purples,
            size_max=60
        )
        fig_map1.update_geos(
            scope="asia", center={"lat":35,"lon":105}, projection_scale=5,
            showland=True, landcolor="#f1f5f9", countrycolor="#cbd5e1",
            bgcolor='rgba(0,0,0,0)'
        )
        fig_map1.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#334155'),
            height=500,
            margin=dict(r=0,t=30,l=0,b=0)
        )
        st.plotly_chart(fig_map1, use_container_width=True)
    
    with m2:
        fig_map2 = px.scatter_geo(
            overseas_data, lat="纬度", lon="经度", size="营收(亿元)",
            hover_name="地区名称", projection="natural earth",
            title="海外大区营收分布",
            color="地区名称",
            color_discrete_map={"东南亚":"#6366f1","欧美":"#ec4899","其他海外地区":"#06b6d4"},
            size_max=60
        )
        fig_map2.update_geos(
            showland=True, landcolor="#f1f5f9", countrycolor="#cbd5e1",
            bgcolor='rgba(0,0,0,0)'
        )
        fig_map2.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#334155'),
            height=500,
            margin=dict(r=0,t=30,l=0,b=0)
        )
        st.plotly_chart(fig_map2, use_container_width=True)

else:
    st.subheader("📊 业务板块与地区分布")
    st.info(f"详细业务板块和全球地区分布数据仅支持腾讯控股，当前分析公司为{main_company}。")

st.markdown('</div>', unsafe_allow_html=True)

# ========== 财务指数专项分析 ==========
st.markdown('<div class="premium-card">', unsafe_allow_html=True)
st.subheader("📉 多项财务指数走势对比")

fig_idx = go.Figure()
indices = [
    ("毛利率%", "#6366f1"),
    ("净利润率%", "#ec4899"),
    ("资产负债率%", "#06b6d4"),
    ("净资产收益率%", "#10b981")
]
for name, color in indices:
    rgb = tuple(int(color.lstrip("#")[i:i+2], 16) for i in (0,2,4))
    fig_idx.add_trace(go.Scatter(
        x=main_data["年份"], y=main_data[name], name=name,
        line=dict(color=color, width=3),
        fill='tozeroy',
        fillcolor=f'rgba{rgb + (0.08,)}',
        marker=dict(size=8)
    ))

fig_idx.update_layout(
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(color='#334155'),
    height=470,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    xaxis=dict(gridcolor='rgba(148,163,184,0.12)'),
    yaxis=dict(gridcolor='rgba(148,163,184,0.12)', zeroline=False)
)
st.plotly_chart(fig_idx, use_container_width=True)

with st.expander("💡 查看财务指数深度分析"):
    st.markdown('''
    <div class="analysis-box">
        <h4>📉 财务健康度综合评估</h4>
        <p><strong>盈利能力：</strong>毛利率保持高位，体现出强大的定价权和成本控制能力。</p>
        <p><strong>偿债能力：</strong>资产负债率维持在健康区间，财务结构稳健。</p>
        <p><strong>运营效率：</strong>ROE表现优异，股东回报能力强。</p>
    </div>
    ''', unsafe_allow_html=True)

# 资产结构面积图
st.subheader("🏦 资产与负债权益结构")
asset_df = main_data[["年份","总负债","股东权益"]].melt(id_vars="年份", var_name="构成", value_name="金额")
fig_asset = px.area(
    asset_df, x="年份", y="金额", color="构成",
    color_discrete_map={"总负债":"#ec4899", "股东权益":"#6366f1"}
)
fig_asset.update_traces(stackgroup='one')
fig_asset.update_layout(
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(color='#334155'),
    height=420,
    xaxis=dict(gridcolor='rgba(148,163,184,0.12)'),
    yaxis=dict(gridcolor='rgba(148,163,184,0.12)', zeroline=False)
)
st.plotly_chart(fig_asset, use_container_width=True)

# 五维能力雷达图
st.subheader("🎯 财务五维能力评估")
radar_vals = [
    year_detail["毛利率%"] / 50 * 100,
    year_detail["净资产收益率%"] / 30 * 100,
    100 - year_detail["资产负债率%"],
    max(year_detail["营收同比增速%"], 0) if not pd.isna(year_detail["营收同比增速%"]) else 0,
    year_detail["资产周转率"] * 100
]
fig_radar_single = go.Figure(go.Scatterpolar(
    r=radar_vals,
    theta=["盈利能力","收益水平","偿债安全","增长潜力","运营效率"],
    fill="toself",
    name="综合评分",
    line=dict(color="#6366f1", width=2.5),
    fillcolor='rgba(99, 102, 241, 0.2)'
))
fig_radar_single.update_layout(
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(color='#334155'),
    height=500,
    polar=dict(
        radialaxis=dict(visible=True, range=[0,100], gridcolor='rgba(148,163,184,0.12)'),
        bgcolor='rgba(255,255,255,0.5)'
    )
)
st.plotly_chart(fig_radar_single, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# ========== 原始数据表 ==========
st.markdown('<div class="premium-card">', unsafe_allow_html=True)
st.subheader("📋 完整原始财务数据表")
st.dataframe(main_data.round(2), use_container_width=True, hide_index=True)
if main_company == "腾讯控股":
    st.subheader("📋 中国34省营收分布数据")
    st.dataframe(province_full_data.round(2), use_container_width=True, hide_index=True)
st.markdown('</div>', unsafe_allow_html=True)

# ========== 二维码（可选） ==========
if QRCODE_AVAILABLE:
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
        st.subheader("📱 手机扫码直接访问")
        
        def generate_qr_code(url):
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=10,
                border=4,
            )
            qr.add_data(url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="#6366f1", back_color="white")
            buf = BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            return buf
        
        app_url = st.secrets.get("app_url", "https://tengxun50-dcnnqxiwj8blzd5e2bvn.streamlit.app/")
        qr_img = generate_qr_code(app_url)
        st.image(qr_img, caption="扫码进入财报分析看板", width=200)
        st.markdown('</div>', unsafe_allow_html=True)

# ========== AI智能问答助手 ==========
st.divider()
st.markdown('<div class="premium-card">', unsafe_allow_html=True)

col_avatar, col_title = st.columns([1, 12])
with col_avatar:
    st.markdown('<div class="ai-avatar">🤖</div>', unsafe_allow_html=True)
with col_title:
    st.subheader("财报小助手")
    st.caption("可以用口语提问哦，比如「阿里巴巴2024年营收多少」")

st.markdown("---")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "你好呀😊 我是财报小助手~ 你可以问我腾讯、阿里、百度、网易的任何财报问题，口语化提问就可以哦！"}
    ]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🤖" if msg["role"]=="assistant" else "👤"):
        st.markdown(msg["content"])

user_input = st.chat_input("试试问：阿里巴巴2024年净利润多少？")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)
    
    parsed = parse_user_query(user_input)
    answer = generate_answer(parsed, main_company, select_year, all_data_dict)
    
    st.session_state.messages.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant", avatar="🤖"):
        st.markdown(answer)

st.markdown('</div>', unsafe_allow_html=True)

# ========== 页脚 ==========
st.markdown("""
<div class="footer-section">
    <p>数据来源：公司官方财报 | 更新至2024年</p>
    <p>© 2026 财务数据分析系统 | 仅供参考，不构成投资建议</p>
</div>
""", unsafe_allow_html=True)
