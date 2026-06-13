import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import re
import warnings
warnings.filterwarnings('ignore')

# ===================== 依赖检测 =====================
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

# ===================== 基础配置 =====================
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

# 页面配置
st.set_page_config(
    page_title="互联网公司财报分析看板",
    layout="wide",
    page_icon="📈",
    initial_sidebar_state="expanded"
)

# ===================== 全局样式 =====================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 50%, #e2e8f0 100%);
    font-family: 'Microsoft YaHei', sans-serif;
    color: #0f172a;
}
.main-title {
    font-size: 2.3rem;
    font-weight: 700;
    text-align: center;
    padding: 2rem 0 1.5rem 0;
    color: #0f172a;
    letter-spacing: 3px;
    margin-bottom: 2rem;
}
.premium-card {
    background: #ffffff;
    border-radius: 16px;
    padding: 2rem;
    margin-bottom: 2.2rem;
    box-shadow: 0 4px 20px rgba(15, 23, 42, 0.08);
    border: 1px solid rgba(148, 163, 184, 0.12);
}
.metric-premium {
    background: linear-gradient(145deg, #f8fafc 0%, #f1f5f9 100%);
    border-radius: 14px;
    padding: 1.5rem 1rem;
    text-align: center;
    border: 1px solid rgba(148, 163, 184, 0.15);
}
.metric-value-premium {
    font-size: 1.9rem;
    font-weight: 700;
    color: #1e40af;
    margin: 0.6rem 0;
}
.metric-label-premium {
    font-size: 0.92rem;
    color: #64748b;
}
.point-analysis {
    background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
    border-radius: 12px;
    padding: 1.3rem 1.6rem;
    margin-top: 1.2rem;
    border-left: 4px solid #0ea5e9;
}
.product-card {
    background: #fff;
    border-radius: 14px;
    padding: 1.5rem 1.2rem;
    text-align: center;
    border: 1px solid rgba(148, 163, 184, 0.15);
    margin-bottom: 1rem;
}
.product-icon {font-size: 2.8rem; margin-bottom: 0.8rem;}
.product-name {font-size: 1.1rem; font-weight: 600;}
.product-desc {font-size: 0.85rem; color: #64748b;}
.product-stat {font-size: 0.9rem; font-weight: 600; color: #2563eb;}
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
.footer-section {
    text-align: center;
    color: #64748b;
    padding: 2rem 1rem 4rem 1rem;
    border-top: 1px solid rgba(148, 163, 184, 0.15);
    margin-top: 3rem;
    font-size: 0.9rem;
}
</style>
""", unsafe_allow_html=True)

# ===================== 智能问答函数 =====================
def parse_question(question, main_company, select_year, all_data, competitor_data):
    question = question.strip()
    q = question.lower()
    greetings = ["你好", "您好", "hi", "hello", "在吗", "嗨"]
    if any(g in q for g in greetings):
        return "你好👋 财报助手已就绪，可查询营收、利润、毛利率、竞品对比等数据。"

    target_company = main_company
    for alias, full_name in company_alias.items():
        if alias in question:
            target_company = full_name
            break

    target_year = select_year
    year_match = re.search(r'20\d{2}', question)
    if year_match:
        target_year = int(year_match.group())
    if "去年" in q:
        target_year = select_year - 1

    if target_company == main_company:
        data = all_data
    elif target_company in competitor_data:
        data = competitor_data[target_company]
    else:
        data = all_data
        target_company = main_company

    year_data = data[data["年份"] == target_year]
    if year_data.empty:
        return f"暂无{target_company}{target_year}年数据，请更换年份。"
    row = year_data.iloc[0]

    if any(w in q for w in ["营收", "收入"]):
        return f"{target_company}{target_year}年营业收入：{row['营业收入']:.2f} 亿元，同比{row['营收同比增速%']}%。"
    elif any(w in q for w in ["净利润", "利润"]):
        return f"{target_company}{target_year}年归母净利润：{row['归母净利润']:.2f} 亿元，净利润率 {row['净利润率%']}%。"
    elif any(w in q for w in ["毛利率", "毛利"]):
        return f"{target_company}{target_year}年毛利率：{row['毛利率%']}%。"
    elif any(w in q for w in ["负债", "资产负债率"]):
        return f"{target_company}{target_year}年资产负债率：{row['资产负债率%']}%。"
    elif any(w in q for w in ["roe", "净资产收益率"]):
        return f"{target_company}{target_year}年ROE：{row['净资产收益率%']}%。"
    elif any(w in q for w in ["对比", "竞品"]):
        if len(competitor_data) > 0:
            comp_name = list(competitor_data.keys())[0]
            comp_row = competitor_data[comp_name][competitor_data[comp_name]["年份"] == target_year].iloc[0]
            return f"{target_year}年对比：\n{target_company} 营收{row['营业收入']:.2f}亿，净利{row['归母净利润']:.2f}亿\n{comp_name} 营收{comp_row['营业收入']:.2f}亿，净利{comp_row['归母净利润']:.2f}亿"
        else:
            return "请先在侧边栏选择对比公司。"
    else:
        return f"{target_company}{target_year}年概况：\n营收 {row['营业收入']:.2f} 亿元\n净利 {row['归母净利润']:.2f} 亿元\n毛利率 {row['毛利率%']}%\n资产负债率 {row['资产负债率%']}%"

# ===================== 本地备份数据（稳定数据源） =====================
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

tencent_business_data = pd.DataFrame({
    "年份": [2021, 2022, 2023, 2024],
    "增值服务营收": [2916.71, 2875.59, 2876.44, 3252.08],
    "金融科技及企业服务营收": [1722.00, 1771.52, 2170.39, 2378.52],
    "营销服务营收": [886.69, 827.75, 958.62, 1015.26],
    "中国大陆营收": [4929.04, 4879.10, 5361.33, 5815.36],
    "海外营收": [672.14, 666.42, 728.82, 787.21],
})

tencent_products = [
    {"icon": "💬", "name": "微信 & WeChat", "desc": "国民级社交应用", "stat": "月活 13.8亿+"},
    {"icon": "🐧", "name": "QQ", "desc": "年轻用户社交阵地", "stat": "月活 5.6亿+"},
    {"icon": "🎮", "name": "王者荣耀", "desc": "头部手游", "stat": "日活 1.2亿+"},
    {"icon": "💳", "name": "微信支付", "desc": "移动支付龙头", "stat": "市占率 40%+"},
    {"icon": "☁️", "name": "腾讯云", "desc": "云服务", "stat": "年营收 900亿+"},
    {"icon": "📺", "name": "腾讯视频", "desc": "长视频平台", "stat": "付费会员 1.3亿+"},
    {"icon": "🎵", "name": "腾讯音乐", "desc": "在线音乐平台", "stat": "月活 5.8亿+"},
    {"icon": "🏢", "name": "企业微信", "desc": "办公协同工具", "stat": "服务企业 1200万+"}
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
    {"name": "Z世代学生群体", "tag": "tag-purple", "desc": "18-24岁，热衷游戏、社交"},
    {"name": "都市白领群体", "tag": "tag-blue", "desc": "25-40岁，职场主力用户"},
    {"name": "下沉市场群体", "tag": "tag-green", "desc": "三四线及县域用户"},
    {"name": "银发老年群体", "tag": "tag-orange", "desc": "50岁以上中老年用户"},
    {"name": "企业B端用户", "tag": "tag-cyan", "desc": "政企办公服务用户"}
]

year_analysis = {
    2021: {"revenue":"业绩高位，多业务高速增长","profit":"净利润处于峰值"},
    2022: {"revenue":"营收小幅承压，行业调整期","profit":"利润阶段性下滑"},
    2023: {"revenue":"重回增长，广告与云业务回暖","profit":"利润阶段性触底"},
    2024: {"revenue":"营收稳步创新高","profit":"利润大幅反弹，盈利修复"}
}

# ===================== 侧边栏 =====================
with st.sidebar:
    st.header("🎛️ 财报分析控制台")
    data_source = st.radio("数据来源", ["本地备份数据"])
    main_company = st.selectbox("选择主分析公司", all_company_list, index=0)
    available_competitors = [c for c in all_company_list if c != main_company]
    competitors = st.multiselect("选择对比公司", available_competitors, default=available_competitors[:2])
    year_list = [2021, 2022, 2023, 2024]
    select_year = st.select_slider("选择查看年份", options=year_list, value=max(year_list))
    if ARIMA_AVAILABLE:
        forecast_years = st.slider("预测未来年数", 1, 5, 3)
    else:
        st.info("预测功能需安装 statsmodels")
        forecast_years = 0
    st.divider()
    st.info("点击图表数据点可查看年度解析")

# ===================== 数据计算 =====================
@st.cache_data
def load_company_data(company_name):
    return backup_data[company_name]

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

main_data = load_company_data(main_company)
main_data = calc_financial_indices(main_data)

competitor_data_dict = {}
for comp in competitors:
    c_df = load_company_data(comp)
    competitor_data_dict[comp] = calc_financial_indices(c_df)

filtered_year_data = main_data[main_data["年份"] == select_year]
year_detail = filtered_year_data.iloc[0] if not filtered_year_data.empty else main_data.iloc[-1]

def safe_display(value, suffix="%"):
    if pd.isna(value):
        return "—"
    return f"{value}{suffix}"

# ===================== 页面主体 =====================
st.markdown(f'<div class="main-title">📈 {main_company} 财报综合数据分析看板</div>', unsafe_allow_html=True)

# 1. 核心指标
st.markdown('<div class="premium-card">', unsafe_allow_html=True)
st.subheader("📊 当期核心财务指标")
m1, m2, m3, m4 = st.columns(4)
m5, m6, m7, m8 = st.columns(4)

with m1:
    st.markdown(f'<div class="metric-premium"><div class="metric-label-premium">营业收入</div><div class="metric-value-premium">¥{year_detail["营业收入"]:,.2f}亿</div></div>', unsafe_allow_html=True)
with m2:
    st.markdown(f'<div class="metric-premium"><div class="metric-label-premium">净利润率</div><div class="metric-value-premium">{year_detail["净利润率%"]}%</div></div>', unsafe_allow_html=True)
with m3:
    st.markdown(f'<div class="metric-premium"><div class="metric-label-premium">毛利率</div><div class="metric-value-premium">{year_detail["毛利率%"]}%</div></div>', unsafe_allow_html=True)
with m4:
    st.markdown(f'<div class="metric-premium"><div class="metric-label-premium">净资产收益率</div><div class="metric-value-premium">{year_detail["净资产收益率%"]}%</div></div>', unsafe_allow_html=True)

rev_color = "#16a34a" if year_detail["营收同比增速%"] >= 0 else "#dc2626"
profit_color = "#16a34a" if year_detail["净利润同比增速%"] >= 0 else "#dc2626"

with m5:
    st.markdown(f'<div class="metric-premium"><div class="metric-label-premium">营收增速</div><div class="metric-value-premium" style="color:{rev_color}">{safe_display(year_detail["营收同比增速%"])}</div></div>', unsafe_allow_html=True)
with m6:
    st.markdown(f'<div class="metric-premium"><div class="metric-label-premium">净利润增速</div><div class="metric-value-premium" style="color:{profit_color}">{safe_display(year_detail["净利润同比增速%"])}</div></div>', unsafe_allow_html=True)
with m7:
    st.markdown(f'<div class="metric-premium"><div class="metric-label-premium">资产负债率</div><div class="metric-value-premium">{year_detail["资产负债率%"]}%</div></div>', unsafe_allow_html=True)
with m8:
    st.markdown(f'<div class="metric-premium"><div class="metric-label-premium">资产周转率</div><div class="metric-value-premium">{year_detail["资产周转率"]}</div></div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# 2. 趋势图（完全删除 smoothing 相关报错参数）
st.markdown('<div class="premium-card">', unsafe_allow_html=True)
st.subheader("📈 营收与净利润历年变化趋势")

fig_trend = go.Figure()
# 营收曲线：仅保留基础参数，移除所有废弃参数
fig_trend.add_trace(go.Scatter(
    x=main_data["年份"],
    y=main_data["营业收入"],
    name="营业收入(亿元)",
    line=dict(color="#2563eb", width=4),
    marker=dict(size=12, color="#2563eb"),
    fill='tozeroy',
    fillcolor='rgba(37, 99, 235, 0.1)'
))
# 净利润曲线
fig_trend.add_trace(go.Scatter(
    x=main_data["年份"],
    y=main_data["归母净利润"],
    name="归母净利润(亿元)",
    yaxis="y2",
    line=dict(color="#8b5cf6", width=4),
    marker=dict(size=12, color="#8b5cf6"),
    fill='tozeroy',
    fillcolor='rgba(139, 92, 246, 0.1)'
))

fig_trend.update_layout(
    height=560,
    yaxis=dict(title="营业收入(亿元)"),
    yaxis2=dict(title="归母净利润(亿元)", overlaying="y", side="right"),
    plot_bgcolor="white",
    paper_bgcolor="white"
)

trend_select = st.plotly_chart(fig_trend, use_container_width=True, on_select="rerun", selection_mode="points")

if trend_select.selection.points:
    p_year = int(trend_select.selection.points[0]["x"])
    p_data = main_data[main_data["年份"] == p_year]
    if not p_data.empty:
        row = p_data.iloc[0]
        st.markdown(f'''
        <div class="point-analysis">
        <h4>{p_year}年经营解析</h4>
        <p>营收：{row["营业收入"]:.2f} 亿元，{year_analysis.get(p_year,{}).get("revenue","经营平稳")}</p>
        <p>净利润：{row["归母净利润"]:.2f} 亿元，{year_analysis.get(p_year,{}).get("profit","盈利稳定")}</p>
        </div>
        ''', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# 3. 竞品对比
if len(competitors) > 0:
    st.markdown('<div class="premium-card">', unsafe_allow_html=True)
    st.subheader("🏆 竞品横向对比")
    c1, c2 = st.columns(2)
    with c1:
        fig_rev = go.Figure()
        fig_rev.add_trace(go.Bar(x=main_data["年份"], y=main_data["营业收入"], name=main_company))
        for name, df in competitor_data_dict.items():
            fig_rev.add_trace(go.Bar(x=df["年份"], y=df["营业收入"], name=name))
        fig_rev.update_layout(barmode="group", title="营业收入对比(亿元)", height=450)
        st.plotly_chart(fig_rev, use_container_width=True)
    with c2:
        fig_profit = go.Figure()
        fig_profit.add_trace(go.Bar(x=main_data["年份"], y=main_data["归母净利润"], name=main_company))
        for name, df in competitor_data_dict.items():
            fig_profit.add_trace(go.Bar(x=df["年份"], y=df["归母净利润"], name=name))
        fig_profit.update_layout(barmode="group", title="净利润对比(亿元)", height=450)
        st.plotly_chart(fig_profit, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# 4. 业务&产品&用户（仅腾讯）
if main_company == "腾讯控股":
    st.markdown('<div class="premium-card">', unsafe_allow_html=True)
    st.subheader("📊 业务板块营收")
    b1, b2 = st.columns(2)
    biz_melt = tencent_business_data.melt(id_vars="年份", value_vars=["增值服务营收","金融科技及企业服务营收","营销服务营收"], var_name="板块", value_name="营收")
    with b1:
        fig_biz = px.bar(biz_melt, x="年份", y="营收", color="板块", barmode="group", height=450)
        st.plotly_chart(fig_biz, use_container_width=True)
    with b2:
        curr_biz = tencent_business_data[tencent_business_data["年份"] == select_year].iloc[0]
        pie_df = pd.DataFrame({
            "板块":["增值服务","金融科技及企业服务","营销服务"],
            "营收":[curr_biz["增值服务营收"],curr_biz["金融科技及企业服务营收"],curr_biz["营销服务营收"]]
        })
        fig_pie = px.pie(pie_df, values="营收", names="板块", hole=0.5, height=450)
        st.plotly_chart(fig_pie, use_container_width=True)

    st.divider()
    st.subheader("🧩 核心产品矩阵")
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
    st.subheader("👥 用户画像")
    u1, u2 = st.columns(2)
    with u1:
        fig_age = px.pie(user_age_data, values="占比%", names="年龄段", hole=0.45, height=450)
        st.plotly_chart(fig_age, use_container_width=True)
    with u2:
        fig_city = px.bar(user_city_data, x="城市等级", y="占比%", height=450)
        st.plotly_chart(fig_city, use_container_width=True)

    st.subheader("核心用户群体")
    for g in user_groups:
        st.markdown(f'<span class="user-tag {g["tag"]}">{g["name"]}</span> {g["desc"]}', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# 5. 财务指标走势
st.markdown('<div class="premium-card">', unsafe_allow_html=True)
st.subheader("📉 财务指标走势")
fig_idx = go.Figure()
fig_idx.add_trace(go.Scatter(x=main_data["年份"], y=main_data["毛利率%"], name="毛利率%", line=dict(width=3)))
fig_idx.add_trace(go.Scatter(x=main_data["年份"], y=main_data["净利润率%"], name="净利润率%", line=dict(width=3)))
fig_idx.add_trace(go.Scatter(x=main_data["年份"], y=main_data["净资产收益率%"], name="ROE%", line=dict(width=3)))
fig_idx.add_trace(go.Scatter(x=main_data["年份"], y=main_data["资产负债率%"], name="资产负债率%", line=dict(width=3)))
fig_idx.update_layout(height=480)
st.plotly_chart(fig_idx, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# 6. 原始数据表格
st.markdown('<div class="premium-card">', unsafe_allow_html=True)
st.subheader("📋 完整财务数据表")
st.dataframe(main_data.round(2), use_container_width=True, hide_index=True)
st.markdown('</div>', unsafe_allow_html=True)

# 7. 智能问答
st.markdown('<div class="premium-card">', unsafe_allow_html=True)
st.subheader("🤖 财报智能问答")
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("输入问题查询财报数据")
if user_input:
    st.session_state.chat_history.append({"role":"user","content":user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
    ans = parse_question(user_input, main_company, select_year, main_data, competitor_data_dict)
    st.session_state.chat_history.append({"role":"assistant","content":ans})
    with st.chat_message("assistant"):
        st.markdown(ans)
st.markdown('</div>', unsafe_allow_html=True)

# 页脚
st.markdown('''
<div class="footer-section">
<p>数据仅供学习参考，不构成投资建议</p>
</div>
''', unsafe_allow_html=True)
