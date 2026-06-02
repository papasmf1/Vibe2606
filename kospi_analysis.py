import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import warnings
warnings.filterwarnings('ignore')

# ─────────────────────────────────────────────
# 한글 폰트 설정
# ─────────────────────────────────────────────
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# ─────────────────────────────────────────────
# 1. 데이터 로드 & 클랜징
# ─────────────────────────────────────────────
df = pd.read_csv('kospi_data.csv')

print("=" * 60)
print("【1】 원본 데이터 기본 정보")
print("=" * 60)
print(f"  원본 행 수       : {len(df):,}")
print(f"  원본 컬럼        : {list(df.columns)}")
print(f"  결측치 현황      :\n{df.isnull().sum()}")

# 날짜 파싱 & 정렬
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
before = len(df)
df.dropna(subset=['Date'], inplace=True)   # 날짜 파싱 실패 행 제거
df.sort_values('Date', inplace=True)
df.reset_index(drop=True, inplace=True)

# 중복 날짜 제거 (마지막 값 유지)
dup_count = df.duplicated(subset=['Date']).sum()
df.drop_duplicates(subset=['Date'], keep='last', inplace=True)
df.reset_index(drop=True, inplace=True)

# 음수·0 값 제거 (가격 컬럼)
price_cols = ['Open', 'High', 'Low', 'Close', 'Adj Close']
mask_negative = (df[price_cols] <= 0).any(axis=1)
df = df[~mask_negative].copy()

# ─── IQR 기반 이상치 탐지 (Close) ───
Q1 = df['Close'].quantile(0.25)
Q3 = df['Close'].quantile(0.75)
IQR = Q3 - Q1
lower_bound = Q1 - 3 * IQR
upper_bound = Q3 + 3 * IQR
outlier_mask = (df['Close'] < lower_bound) | (df['Close'] > upper_bound)
outlier_count = outlier_mask.sum()

print(f"\n  IQR 이상치(Close) : {outlier_count}건 → 보존(극단값이지만 실제 시장 데이터)")

# 논리 검증: Low <= Close <= High
invalid = ((df['Close'] < df['Low']) | (df['Close'] > df['High'])).sum()
print(f"  가격 논리 오류    : {invalid}건")

print(f"\n  중복 날짜 제거    : {dup_count}건")
print(f"  유효 레코드 수    : {len(df):,}")

# ─────────────────────────────────────────────
# 2. 2000~2019 필터링
# ─────────────────────────────────────────────
df_full = df.copy()
df = df[(df['Date'] >= '2000-01-01') & (df['Date'] <= '2019-12-31')].copy()
df.reset_index(drop=True, inplace=True)

print(f"\n  분석 범위(2000~2019) 레코드 : {len(df):,}")
print(f"  시작일 : {df['Date'].min().date()}  /  종료일 : {df['Date'].max().date()}")

# 파생 컬럼
df['Year']      = df['Date'].dt.year
df['Month']     = df['Date'].dt.month
df['YearMonth'] = df['Date'].dt.to_period('M')

# 일간 수익률
df['Daily_Return'] = df['Close'].pct_change()

print("\n  클랜징 완료 ✓")

# ─────────────────────────────────────────────
# 3. 연도별 요약 통계
# ─────────────────────────────────────────────
yearly = df.groupby('Year')['Close'].agg(['first', 'last', 'max', 'min', 'mean', 'std'])
yearly.columns = ['연초', '연말', '최고', '최저', '평균', '표준편차']
yearly['연간수익률(%)'] = ((yearly['연말'] / yearly['연초']) - 1) * 100

print("\n" + "=" * 60)
print("【2】 연도별 KOSPI 200 통계 (2000~2019)")
print("=" * 60)
print(yearly.round(2).to_string())

# ─────────────────────────────────────────────
# 시각화 (6개 차트)
# ─────────────────────────────────────────────
fig = plt.figure(figsize=(20, 24))
fig.suptitle('KOSPI 200 지수 다각도 분석 (2000년 1월 ~ 2019년 12월)', 
             fontsize=18, fontweight='bold', y=0.98)

# ── 팔레트 ──
c_main   = '#1565C0'
c_bull   = '#E53935'
c_bear   = '#1976D2'
c_ma50   = '#FF6F00'
c_ma200  = '#7B1FA2'
c_vol    = '#546E7A'

# ────────────────────────────────────────────
# 차트 ① : Close 라인그래프 + 이동평균
# ────────────────────────────────────────────
ax1 = fig.add_subplot(4, 2, (1, 2))   # 상단 전체 폭

df['MA50']  = df['Close'].rolling(50).mean()
df['MA200'] = df['Close'].rolling(200).mean()

ax1.fill_between(df['Date'], df['Close'], alpha=0.08, color=c_main)
ax1.plot(df['Date'], df['Close'],  color=c_main,  lw=1.2, label='KOSPI 200 종가')
ax1.plot(df['Date'], df['MA50'],   color=c_ma50,  lw=1.0, linestyle='--', label='50일 이동평균')
ax1.plot(df['Date'], df['MA200'],  color=c_ma200, lw=1.0, linestyle=':',  label='200일 이동평균')

# 주요 이벤트 주석
events = {
    '2000-03': ('IT버블\n붕괴',    0.02),
    '2003-03': ('이라크\n전쟁',   -0.05),
    '2008-09': ('글로벌\n금융위기', 0.02),
    '2011-08': ('유럽\n재정위기',  -0.05),
    '2016-01': ('중국\n쇼크',      0.02),
}
for ym, (label, yoff_ratio) in events.items():
    dt = pd.Timestamp(ym)
    row = df[df['Date'] >= dt]
    if not row.empty:
        idx_val = row.iloc[0]['Close']
        ax1.annotate(label, xy=(dt, idx_val),
                     xytext=(dt, idx_val * (1 + yoff_ratio + 0.12)),
                     fontsize=7.5, ha='center', color='#B71C1C',
                     arrowprops=dict(arrowstyle='->', color='#B71C1C', lw=0.8))

ax1.set_title('① KOSPI 200 종가 추이 (종가 기준 라인그래프)', fontsize=12, fontweight='bold')
ax1.set_ylabel('지수 (포인트)')
ax1.legend(loc='upper left', fontsize=9)
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
ax1.grid(True, alpha=0.3)
ax1.set_xlim(df['Date'].min(), df['Date'].max())

# ────────────────────────────────────────────
# 차트 ② : 연간 수익률 바 차트
# ────────────────────────────────────────────
ax2 = fig.add_subplot(4, 2, 3)
colors_bar = [c_bull if v >= 0 else c_bear for v in yearly['연간수익률(%)']]
bars = ax2.bar(yearly.index, yearly['연간수익률(%)'], color=colors_bar, edgecolor='white', linewidth=0.5)
ax2.axhline(0, color='black', lw=0.8)
for bar, val in zip(bars, yearly['연간수익률(%)']):
    ax2.text(bar.get_x() + bar.get_width()/2, 
             bar.get_height() + (1.5 if val >= 0 else -3.5),
             f'{val:.1f}%', ha='center', va='bottom', fontsize=7)
ax2.set_title('② 연간 수익률 (%)', fontsize=11, fontweight='bold')
ax2.set_ylabel('%')
ax2.set_xticks(yearly.index)
ax2.set_xticklabels(yearly.index, rotation=45, fontsize=8)
ax2.grid(axis='y', alpha=0.3)

# ────────────────────────────────────────────
# 차트 ③ : 월별 평균 수익률 (계절성)
# ────────────────────────────────────────────
ax3 = fig.add_subplot(4, 2, 4)
month_ret = df.groupby('Month')['Daily_Return'].mean() * 100
month_labels = ['1월','2월','3월','4월','5월','6월','7월','8월','9월','10월','11월','12월']
colors_m = [c_bull if v >= 0 else c_bear for v in month_ret]
ax3.bar(month_labels, month_ret, color=colors_m, edgecolor='white')
ax3.axhline(0, color='black', lw=0.8)
ax3.set_title('③ 월별 평균 일간 수익률 (계절성)', fontsize=11, fontweight='bold')
ax3.set_ylabel('평균 일간 수익률 (%)')
ax3.tick_params(axis='x', labelsize=8)
ax3.grid(axis='y', alpha=0.3)

# ────────────────────────────────────────────
# 차트 ④ : 롤링 변동성 (60일 표준편차 × √252)
# ────────────────────────────────────────────
ax4 = fig.add_subplot(4, 2, 5)
df['Volatility'] = df['Daily_Return'].rolling(60).std() * np.sqrt(252) * 100
ax4.fill_between(df['Date'], df['Volatility'], alpha=0.4, color=c_vol)
ax4.plot(df['Date'], df['Volatility'], color=c_vol, lw=0.9)
ax4.set_title('④ 60일 롤링 연환산 변동성 (%)', fontsize=11, fontweight='bold')
ax4.set_ylabel('변동성 (%)')
ax4.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:.0f}%'))
ax4.grid(True, alpha=0.3)
ax4.set_xlim(df['Date'].min(), df['Date'].max())

# ────────────────────────────────────────────
# 차트 ⑤ : 낙폭 (Drawdown)
# ────────────────────────────────────────────
ax5 = fig.add_subplot(4, 2, 6)
rolling_max = df['Close'].cummax()
drawdown    = (df['Close'] - rolling_max) / rolling_max * 100
ax5.fill_between(df['Date'], drawdown, 0, alpha=0.5, color='#C62828')
ax5.plot(df['Date'], drawdown, color='#C62828', lw=0.8)
max_dd = drawdown.min()
max_dd_date = df.loc[drawdown.idxmin(), 'Date']
ax5.annotate(f'최대낙폭\n{max_dd:.1f}%',
             xy=(max_dd_date, max_dd),
             xytext=(max_dd_date + pd.Timedelta(days=300), max_dd + 10),
             fontsize=8, color='#B71C1C',
             arrowprops=dict(arrowstyle='->', color='#B71C1C'))
ax5.set_title('⑤ 최고점 대비 낙폭 (Drawdown)', fontsize=11, fontweight='bold')
ax5.set_ylabel('낙폭 (%)')
ax5.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:.0f}%'))
ax5.grid(True, alpha=0.3)
ax5.set_xlim(df['Date'].min(), df['Date'].max())

# ────────────────────────────────────────────
# 차트 ⑥ : 연도별 박스플롯 (Close)
# ────────────────────────────────────────────
ax6 = fig.add_subplot(4, 2, 7)
box_data = [df[df['Year'] == y]['Close'].values for y in sorted(df['Year'].unique())]
bp = ax6.boxplot(box_data, patch_artist=True, 
                 medianprops=dict(color='white', linewidth=1.5),
                 whiskerprops=dict(linewidth=0.8),
                 capprops=dict(linewidth=0.8))
for patch in bp['boxes']:
    patch.set_facecolor(c_main)
    patch.set_alpha(0.6)
ax6.set_xticklabels(sorted(df['Year'].unique()), rotation=45, fontsize=8)
ax6.set_title('⑥ 연도별 종가 분포 (Box Plot)', fontsize=11, fontweight='bold')
ax6.set_ylabel('지수 (포인트)')
ax6.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
ax6.grid(axis='y', alpha=0.3)

# ────────────────────────────────────────────
# 차트 ⑦ : 일간 수익률 히스토그램
# ────────────────────────────────────────────
ax7 = fig.add_subplot(4, 2, 8)
ret = df['Daily_Return'].dropna() * 100
ax7.hist(ret, bins=80, color=c_main, edgecolor='white', alpha=0.7, density=True)

# 정규분포 커브 (numpy로 직접 계산)
mu, sigma = ret.mean(), ret.std()
xmin, xmax = ret.min(), ret.max()
x = np.linspace(xmin, xmax, 200)
normal_pdf = (1 / (sigma * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mu) / sigma) ** 2)
ax7.plot(x, normal_pdf, color='red', lw=1.5, label=f'정규분포 (μ={mu:.3f}, σ={sigma:.3f})')
ax7.axvline(ret.mean(), color='orange', linestyle='--', lw=1.2, label=f'평균={ret.mean():.3f}%')
ax7.set_title('⑦ 일간 수익률 분포 (히스토그램)', fontsize=11, fontweight='bold')
ax7.set_xlabel('일간 수익률 (%)')
ax7.set_ylabel('밀도')
ax7.legend(fontsize=8)
ax7.grid(axis='y', alpha=0.3)

plt.tight_layout(rect=[0, 0, 1, 0.97])
plt.savefig('kospi_analysis.png', dpi=150, bbox_inches='tight')
print("\n  그래프 저장: kospi_analysis.png")
plt.show()

# ─────────────────────────────────────────────
# 4. 종합 요약
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("【3】 종합 분석 요약 (2000~2019)")
print("=" * 60)
total_ret = (df['Close'].iloc[-1] / df['Close'].iloc[0] - 1) * 100
cagr      = ((df['Close'].iloc[-1] / df['Close'].iloc[0]) ** (1/20) - 1) * 100
ann_vol   = df['Daily_Return'].std() * np.sqrt(252) * 100
sharpe    = (cagr / ann_vol)
max_close = df['Close'].max()
min_close = df['Close'].min()

print(f"  분석 기간        : {df['Date'].min().date()} ~ {df['Date'].max().date()} (약 20년)")
print(f"  시작 지수        : {df['Close'].iloc[0]:,.2f}")
print(f"  종료 지수        : {df['Close'].iloc[-1]:,.2f}")
print(f"  기간 총 수익률   : {total_ret:.2f}%")
print(f"  연평균 수익률    : {cagr:.2f}% (CAGR)")
print(f"  연환산 변동성    : {ann_vol:.2f}%")
print(f"  Sharpe Ratio     : {sharpe:.3f} (무위험이자율=0 가정)")
print(f"  20년 최고가      : {max_close:,.2f}  ({df.loc[df['Close'].idxmax(),'Date'].date()})")
print(f"  20년 최저가      : {min_close:,.2f}  ({df.loc[df['Close'].idxmin(),'Date'].date()})")
print(f"  최대 낙폭(MDD)   : {drawdown.min():.2f}%  ({max_dd_date.date()})")
print(f"  양봉일 비율      : {(df['Daily_Return']>0).mean()*100:.1f}%")
print(f"  일간수익률 왜도  : {df['Daily_Return'].skew():.4f}  (음수=왼쪽 두꺼운 꼬리)")
print(f"  일간수익률 첨도  : {df['Daily_Return'].kurt():.4f}  (>3이면 뾰족한 분포)")
