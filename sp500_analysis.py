"""
S&P 500 과거 데이터 분석 (2000년 1월 ~ 2019년 12월)
- 데이터 클렌징
- 종가 기준 라인그래프 및 다각도 분석
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.patches import FancyArrowPatch
import warnings
warnings.filterwarnings('ignore')

# ────────────────────────────────────────────────
# 한글 폰트 설정
# ────────────────────────────────────────────────
import matplotlib
matplotlib.rcParams['font.family'] = 'Malgun Gothic'
matplotlib.rcParams['axes.unicode_minus'] = False

# ────────────────────────────────────────────────
# 1. 데이터 로드
# ────────────────────────────────────────────────
print("=" * 60)
print("▶ 1단계: 데이터 로드")
print("=" * 60)

df_raw = pd.read_csv(
    r"c:\work\S&P 500 과거 데이터.csv",
    encoding='utf-8-sig'
)
print(f"원본 행수: {len(df_raw):,}행  /  컬럼: {list(df_raw.columns)}")
print(df_raw.head(3))

# ────────────────────────────────────────────────
# 2. 데이터 클렌징
# ────────────────────────────────────────────────
print("\n" + "=" * 60)
print("▶ 2단계: 데이터 클렌징")
print("=" * 60)

df = df_raw.copy()

# 컬럼명 정리
df.columns = ['날짜', '종가', '시가', '고가', '저가', '거래량', '변동률']

# (1) 날짜 파싱: "2019- 11- 14" → "2019-11-14"
df['날짜'] = df['날짜'].str.replace(r'\s+', '', regex=True)
df['날짜'] = pd.to_datetime(df['날짜'], format='%Y-%m-%d', errors='coerce')

# (2) 숫자형 컬럼 정리: 쉼표 제거 후 float 변환
for col in ['종가', '시가', '고가', '저가']:
    df[col] = df[col].astype(str).str.replace(',', '', regex=False)
    df[col] = pd.to_numeric(df[col], errors='coerce')

# (3) 변동률: "0.08%" → 0.08
df['변동률'] = (
    df['변동률']
    .astype(str)
    .str.replace('%', '', regex=False)
    .str.strip()
)
df['변동률'] = pd.to_numeric(df['변동률'], errors='coerce')

# (4) 거래량: 빈 문자열 → NaN
df['거래량'] = pd.to_numeric(
    df['거래량'].astype(str).str.replace(',', '', regex=False),
    errors='coerce'
)

# (5) 날짜 결측 제거
before = len(df)
df = df.dropna(subset=['날짜', '종가'])
print(f"날짜·종가 결측 제거: {before - len(df)}행 삭제, 잔여 {len(df):,}행")

# (6) 중복 날짜 제거
dup = df.duplicated(subset=['날짜']).sum()
if dup > 0:
    df = df.drop_duplicates(subset=['날짜'], keep='first')
    print(f"중복 날짜 {dup}건 제거")

# (7) 날짜 오름차순 정렬
df = df.sort_values('날짜').reset_index(drop=True)

# (8) 2000-01-01 ~ 2019-12-31 필터링
df = df[(df['날짜'] >= '2000-01-01') & (df['날짜'] <= '2019-12-31')]
df = df.reset_index(drop=True)

print(f"\n분석 기간: {df['날짜'].min().date()} ~ {df['날짜'].max().date()}")
print(f"총 거래일: {len(df):,}일")
print(f"\n[기초 통계]")
print(df['종가'].describe().round(2))

# 파생 컬럼 생성
df['연도'] = df['날짜'].dt.year
df['월'] = df['날짜'].dt.month
df['연월'] = df['날짜'].dt.to_period('M')

# 일간 수익률
df['일간수익률'] = df['종가'].pct_change() * 100

# 누적 수익률 (2000년 첫 거래일 기준)
df['누적수익률'] = (df['종가'] / df['종가'].iloc[0] - 1) * 100

# 이동평균
df['MA50']  = df['종가'].rolling(50).mean()
df['MA200'] = df['종가'].rolling(200).mean()

# 연간 최고점 대비 낙폭(Drawdown)
df['rolling_max'] = df['종가'].cummax()
df['drawdown']    = (df['종가'] - df['rolling_max']) / df['rolling_max'] * 100

# ────────────────────────────────────────────────
# 3. 연간 통계 요약
# ────────────────────────────────────────────────
print("\n" + "=" * 60)
print("▶ 3단계: 연간 통계 요약")
print("=" * 60)

annual = df.groupby('연도').agg(
    시작가=('종가', 'first'),
    종가=('종가', 'last'),
    최고가=('고가', 'max'),
    최저가=('저가', 'min'),
    평균가=('종가', 'mean'),
    변동성=('일간수익률', 'std')
).round(2)
annual['연간수익률(%)'] = ((annual['종가'] / annual['시작가']) - 1) * 100
annual['연간수익률(%)'] = annual['연간수익률(%)'].round(2)
print(annual[['시작가', '종가', '연간수익률(%)', '최고가', '최저가', '변동성']].to_string())

# ────────────────────────────────────────────────
# 4. 시각화 (6개 차트)
# ────────────────────────────────────────────────
print("\n" + "=" * 60)
print("▶ 4단계: 차트 생성")
print("=" * 60)

fig = plt.figure(figsize=(22, 28))
fig.suptitle("S&P 500 심층 분석 (2000년 1월 ~ 2019년 12월)", fontsize=20, fontweight='bold', y=0.98)

colors = {
    '주가': '#1f77b4',
    'MA50': '#ff7f0e',
    'MA200': '#d62728',
    '상승': '#2ca02c',
    '하락': '#d62728',
    '중립': '#7f7f7f',
}

crisis_zones = [
    ('2000-03-01', '2002-10-09', '#ffcccc', 'IT 버블 붕괴\n(2000~2002)'),
    ('2007-10-09', '2009-03-09', '#ffd9b3', '금융위기\n(2008~2009)'),
]

# ─── 차트 1: 종가 + 이동평균 ───────────────────
ax1 = fig.add_subplot(4, 2, (1, 2))
ax1.plot(df['날짜'], df['종가'], color=colors['주가'], linewidth=1.2, label='종가', zorder=3)
ax1.plot(df['날짜'], df['MA50'],  color=colors['MA50'],  linewidth=1.2, linestyle='--', label='50일 이동평균', zorder=2)
ax1.plot(df['날짜'], df['MA200'], color=colors['MA200'], linewidth=1.4, linestyle='-.', label='200일 이동평균', zorder=2)

for s, e, c, lbl in crisis_zones:
    ax1.axvspan(pd.Timestamp(s), pd.Timestamp(e), color=c, alpha=0.45, label=lbl)

ax1.set_title('① 종가 추이 & 이동평균 (50일 / 200일)', fontsize=13, fontweight='bold')
ax1.set_ylabel('지수 (포인트)')
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
ax1.legend(loc='upper left', fontsize=9)
ax1.grid(True, alpha=0.3)
ax1.set_xlim(df['날짜'].min(), df['날짜'].max())

# ─── 차트 2: 누적 수익률 ───────────────────────
ax2 = fig.add_subplot(4, 2, 3)
ax2.fill_between(df['날짜'], df['누적수익률'], 0,
                 where=df['누적수익률'] >= 0, color='#2ca02c', alpha=0.3)
ax2.fill_between(df['날짜'], df['누적수익률'], 0,
                 where=df['누적수익률'] < 0,  color='#d62728', alpha=0.3)
ax2.plot(df['날짜'], df['누적수익률'], color='navy', linewidth=1.2)
ax2.axhline(0, color='black', linewidth=0.8, linestyle='--')
ax2.set_title('② 누적 수익률 (%)', fontsize=12, fontweight='bold')
ax2.set_ylabel('수익률 (%)')
ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:+.0f}%'))
ax2.grid(True, alpha=0.3)
ax2.set_xlim(df['날짜'].min(), df['날짜'].max())

# ─── 차트 3: 연간 수익률 막대 ─────────────────
ax3 = fig.add_subplot(4, 2, 4)
yr_ret = annual['연간수익률(%)']
bar_colors = [colors['상승'] if v >= 0 else colors['하락'] for v in yr_ret]
bars = ax3.bar(yr_ret.index, yr_ret.values, color=bar_colors, edgecolor='white', linewidth=0.5)
ax3.axhline(0, color='black', linewidth=0.8)
for bar, val in zip(bars, yr_ret.values):
    ax3.text(bar.get_x() + bar.get_width()/2,
             val + (1.2 if val >= 0 else -2.2),
             f'{val:+.1f}%', ha='center', va='bottom' if val >= 0 else 'top',
             fontsize=6.5, fontweight='bold')
ax3.set_title('③ 연간 수익률 (%)', fontsize=12, fontweight='bold')
ax3.set_ylabel('수익률 (%)')
ax3.set_xticks(yr_ret.index)
ax3.set_xticklabels(yr_ret.index, rotation=45, fontsize=8)
ax3.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:+.0f}%'))
ax3.grid(True, alpha=0.3, axis='y')

# ─── 차트 4: 낙폭(Drawdown) ───────────────────
ax4 = fig.add_subplot(4, 2, 5)
ax4.fill_between(df['날짜'], df['drawdown'], 0, color='#d62728', alpha=0.5)
ax4.plot(df['날짜'], df['drawdown'], color='darkred', linewidth=0.8)
ax4.set_title('④ 최고점 대비 낙폭 (Drawdown)', fontsize=12, fontweight='bold')
ax4.set_ylabel('낙폭 (%)')
ax4.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:.0f}%'))
ax4.grid(True, alpha=0.3)
ax4.set_xlim(df['날짜'].min(), df['날짜'].max())

# 최대 낙폭 포인트 표시
min_idx = df['drawdown'].idxmin()
ax4.annotate(f"최대 낙폭\n{df.loc[min_idx,'drawdown']:.1f}%\n({df.loc[min_idx,'날짜'].strftime('%Y-%m-%d')})",
             xy=(df.loc[min_idx,'날짜'], df.loc[min_idx,'drawdown']),
             xytext=(pd.Timestamp('2005-01-01'), -48),
             fontsize=8, color='darkred',
             arrowprops=dict(arrowstyle='->', color='darkred', lw=1.2))

# ─── 차트 5: 연간 변동성 (일간수익률 표준편차) ──
ax5 = fig.add_subplot(4, 2, 6)
vol = df.groupby('연도')['일간수익률'].std().reset_index()
vol.columns = ['연도', '변동성']
bar_v = ax5.bar(vol['연도'], vol['변동성'], color='steelblue', edgecolor='white')
ax5.set_title('⑤ 연간 변동성 (일간수익률 표준편차)', fontsize=12, fontweight='bold')
ax5.set_ylabel('표준편차 (%)')
ax5.set_xticks(vol['연도'])
ax5.set_xticklabels(vol['연도'], rotation=45, fontsize=8)
ax5.grid(True, alpha=0.3, axis='y')

# ─── 차트 6: 월별 평균 수익률 히트맵 ─────────
ax6 = fig.add_subplot(4, 2, 7)
monthly_ret = df.pivot_table(
    index='연도', columns='월', values='일간수익률', aggfunc='sum'
)
monthly_ret.columns = ['1월','2월','3월','4월','5월','6월',
                        '7월','8월','9월','10월','11월','12월']

im = ax6.imshow(monthly_ret.values, aspect='auto', cmap='RdYlGn',
                vmin=-15, vmax=15)
plt.colorbar(im, ax=ax6, label='월간 수익률 합계 (%)', shrink=0.8)
ax6.set_xticks(range(12))
ax6.set_xticklabels(monthly_ret.columns, fontsize=8, rotation=45)
ax6.set_yticks(range(len(monthly_ret)))
ax6.set_yticklabels(monthly_ret.index, fontsize=8)
ax6.set_title('⑥ 연도·월별 수익률 히트맵', fontsize=12, fontweight='bold')

for i in range(len(monthly_ret)):
    for j in range(12):
        val = monthly_ret.values[i, j]
        if not np.isnan(val):
            ax6.text(j, i, f'{val:.1f}', ha='center', va='center',
                     fontsize=5.5, color='black')

# ─── 차트 7: 일간 수익률 분포 ─────────────────
ax7 = fig.add_subplot(4, 2, 8)
returns = df['일간수익률'].dropna()
ax7.hist(returns, bins=100, color='steelblue', edgecolor='white',
         alpha=0.7, density=True, label='일간 수익률')

# 정규분포 곡선 오버레이 (numpy로 계산)
mu, sigma = returns.mean(), returns.std()
x = np.linspace(returns.min(), returns.max(), 300)
norm_pdf = (1 / (sigma * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mu) / sigma) ** 2)
ax7.plot(x, norm_pdf, 'r-', linewidth=2, label=f'정규분포 (μ={mu:.3f}, σ={sigma:.3f})')
ax7.axvline(0, color='black', linewidth=0.8, linestyle='--')
ax7.set_title('⑦ 일간 수익률 분포', fontsize=12, fontweight='bold')
ax7.set_xlabel('일간 수익률 (%)')
ax7.set_ylabel('밀도')
ax7.legend(fontsize=8)
ax7.grid(True, alpha=0.3)

# ────────────────────────────────────────────────
plt.tight_layout(rect=[0, 0, 1, 0.97])
plt.savefig(r'c:\work\sp500_analysis.png', dpi=150, bbox_inches='tight')
print("차트 저장: c:\\work\\sp500_analysis.png")
plt.show()

# ────────────────────────────────────────────────
# 5. 핵심 지표 요약 출력
# ────────────────────────────────────────────────
print("\n" + "=" * 60)
print("▶ 5단계: 핵심 지표 요약")
print("=" * 60)

start_price = df['종가'].iloc[0]
end_price   = df['종가'].iloc[-1]
total_return = (end_price / start_price - 1) * 100
max_dd = df['drawdown'].min()
best_year = annual['연간수익률(%)'].idxmax()
worst_year = annual['연간수익률(%)'].idxmin()
avg_daily_vol = df['일간수익률'].std()

print(f"  분석 기간       : {df['날짜'].min().date()} ~ {df['날짜'].max().date()}")
print(f"  시작 지수       : {start_price:,.2f}")
print(f"  종료 지수       : {end_price:,.2f}")
print(f"  총 누적 수익률  : {total_return:+.2f}%")
print(f"  최대 낙폭       : {max_dd:.2f}%  (2009-03-09)")
print(f"  일간 변동성(σ)  : {avg_daily_vol:.4f}%")
print(f"  최고의 해       : {best_year}년 ({annual.loc[best_year,'연간수익률(%)']:+.2f}%)")
print(f"  최악의 해       : {worst_year}년 ({annual.loc[worst_year,'연간수익률(%)']:+.2f}%)")
print(f"  양의 수익률 연도 수: {(annual['연간수익률(%)'] > 0).sum()}년  /  {len(annual)}년")
print("=" * 60)
