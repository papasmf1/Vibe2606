import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import warnings
warnings.filterwarnings('ignore')

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# ──────────────────────────────────────────
# 1. 데이터 로딩
# ──────────────────────────────────────────
FILE = '출생아수__합계출산율__자연증가_등_20260602141803.xlsx'

raw = pd.read_excel(FILE, sheet_name='데이터')
print("=== 원본 데이터 shape:", raw.shape)
print(raw.head())

# ──────────────────────────────────────────
# 2. 데이터 클랜징
# ──────────────────────────────────────────

# 2-1. 전치: 행=연도, 열=지표
df = raw.set_index('기본항목별').T.reset_index()
df.rename(columns={'index': '연도'}, inplace=True)

# 2-2. 연도 컬럼 정제 ('2025 p)' → '2025' 등 공백·주석 제거)
df['연도'] = df['연도'].astype(str).str.extract(r'(\d{4})')[0].astype(int)

# 2-3. 1970~2025 범위 필터링
df = df[(df['연도'] >= 1970) & (df['연도'] <= 2025)].copy()

# 2-4. 컬럼명 단순화
df.rename(columns={
    '출생아수(명)':       '출생아수',
    '합계출산율(명)':     '합계출산율',
    '조출생률(천명당)':   '조출생률',
    '자연증가건수(명)':   '자연증가건수',
    '자연증가율(천명당)': '자연증가율',
    '출생성비(명)':       '출생성비',
}, inplace=True)

# 2-5. 숫자형 변환
numeric_cols = ['출생아수', '합계출산율', '조출생률', '자연증가건수', '자연증가율', '출생성비']
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# 2-6. 결측값 확인 및 처리
print("\n=== 결측값 현황 ===")
print(df[numeric_cols].isnull().sum())
df[numeric_cols] = df[numeric_cols].interpolate(method='linear')

# 2-7. 인덱스 재설정
df.set_index('연도', inplace=True)
df.sort_index(inplace=True)

print("\n=== 클랜징 후 데이터 (처음 5행) ===")
print(df.head())
print("\n=== 기초 통계 ===")
print(df[['출생아수', '합계출산율']].describe().round(2))

# ──────────────────────────────────────────
# 3. 출생아수 라인 그래프
# ──────────────────────────────────────────

fig, axes = plt.subplots(2, 1, figsize=(14, 10))
fig.suptitle('대한민국 출생 동향 (1970–2025)', fontsize=16, fontweight='bold', y=0.98)

# ── 서브플롯 1: 출생아수 (막대 + 라인 겹치기) ──────────────
ax1 = axes[0]

# 특정 구간 색상 구분
colors = []
for yr in df.index:
    if yr <= 1983:
        colors.append('#5B9BD5')   # 고출산 시대 (파랑)
    elif yr <= 2002:
        colors.append('#ED7D31')   # 안정기 (주황)
    else:
        colors.append('#FF4C4C')   # 저출산 심화 (빨강)

ax1.bar(df.index, df['출생아수'] / 10000, color=colors, alpha=0.5, width=0.7, label='출생아수(막대)')
ax1.plot(df.index, df['출생아수'] / 10000, color='#2F5496', linewidth=2, marker='o',
         markersize=4, label='출생아수(추세선)', zorder=5)

# 주요 이벤트 주석
annotations = {
    1970: (1006645, '1970\n100.7만'),
    2002: (496911,  '2002\n49.7만'),
    2015: (438420,  '2015\n43.8만'),
    2023: (230028,  '2023\n23.0만'),
    2025: (254457,  '2025\n25.4만\n(잠정)'),
}
for yr, (val, label) in annotations.items():
    if yr in df.index:
        ax1.annotate(label,
                     xy=(yr, val / 10000),
                     xytext=(yr + 0.3, val / 10000 + 3),
                     fontsize=8, color='#2F5496',
                     arrowprops=dict(arrowstyle='->', color='gray', lw=0.8))

ax1.set_title('연도별 출생아수', fontsize=13, pad=8)
ax1.set_ylabel('출생아수 (만 명)', fontsize=11)
ax1.set_xlim(1969, 2026)
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:.0f}만'))
ax1.legend(loc='upper right', fontsize=9)
ax1.grid(axis='y', linestyle='--', alpha=0.5)

# 색상 범례 (구간 설명)
from matplotlib.patches import Patch
legend_patches = [
    Patch(facecolor='#5B9BD5', alpha=0.6, label='고출산 시대 (~1983)'),
    Patch(facecolor='#ED7D31', alpha=0.6, label='안정기 (1984–2002)'),
    Patch(facecolor='#FF4C4C', alpha=0.6, label='저출산 심화 (2003~)'),
]
ax1.legend(handles=legend_patches, loc='upper right', fontsize=9)

# ── 서브플롯 2: 합계출산율 ──────────────────────────────────
ax2 = axes[1]
ax2.plot(df.index, df['합계출산율'], color='#70AD47', linewidth=2.5, marker='s',
         markersize=4, label='합계출산율')
ax2.axhline(y=2.1, color='red', linestyle='--', linewidth=1.2, label='인구 유지선 (2.1명)')
ax2.axhline(y=1.0, color='orange', linestyle=':', linewidth=1.2, label='초저출산 기준 (1.0명)')

# 최저 기록 강조
min_year = df['합계출산율'].idxmin()
min_val = df['합계출산율'].min()
ax2.annotate(f'최저 {min_val:.3f}명\n({min_year}년)',
             xy=(min_year, min_val),
             xytext=(min_year - 6, min_val + 0.2),
             fontsize=9, color='red',
             arrowprops=dict(arrowstyle='->', color='red', lw=0.8))

ax2.set_title('연도별 합계출산율', fontsize=13, pad=8)
ax2.set_ylabel('합계출산율 (명)', fontsize=11)
ax2.set_xlim(1969, 2026)
ax2.legend(loc='upper right', fontsize=9)
ax2.grid(axis='y', linestyle='--', alpha=0.5)

plt.tight_layout(rect=[0, 0, 1, 0.97])
plt.savefig('birth_analysis.png', dpi=150, bbox_inches='tight')
print("\n그래프 저장 완료: birth_analysis.png")
plt.show()

# ──────────────────────────────────────────
# 4. 추가 통계 출력
# ──────────────────────────────────────────
print("\n=== 연대별 평균 출생아수 ===")
decade_map = {
    '1970년대': range(1970, 1980),
    '1980년대': range(1980, 1990),
    '1990년대': range(1990, 2000),
    '2000년대': range(2000, 2010),
    '2010년대': range(2010, 2020),
    '2020년대': range(2020, 2026),
}
for decade, years in decade_map.items():
    avg = df.loc[df.index.isin(years), '출생아수'].mean()
    print(f"  {decade}: {avg:,.0f}명 ({avg/10000:.1f}만 명)")

print(f"\n=== 1970 대비 2025 감소율 ===")
v1970 = df.loc[1970, '출생아수']
v2025 = df.loc[2025, '출생아수']
print(f"  1970년: {v1970:,.0f}명")
print(f"  2025년: {v2025:,.0f}명")
print(f"  감소율: {(1 - v2025/v1970)*100:.1f}%")
