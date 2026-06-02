import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import urllib.request

# 한글 폰트 설정 (Windows)
matplotlib.rcParams['font.family'] = 'Malgun Gothic'
matplotlib.rcParams['axes.unicode_minus'] = False

# 타이타닉 데이터셋 다운로드 (GitHub 공개 데이터)
url = "https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv"
print("타이타닉 데이터셋 다운로드 중...")
df = pd.read_csv(url)
print(f"데이터 로드 완료: {len(df)}개 행\n")

# 기본 정보 출력
print("=== 데이터 기본 정보 ===")
print(df[['Sex', 'Survived']].value_counts().sort_index())
print()

# 성별 생존 분석
survival_by_sex = df.groupby('Sex')['Survived'].agg(['sum', 'count', 'mean'])
survival_by_sex.columns = ['생존자수', '전체인원', '생존비율']
survival_by_sex['생존비율(%)'] = survival_by_sex['생존비율'] * 100

print("=== 성별 생존율 분석 ===")
print(survival_by_sex[['생존자수', '전체인원', '생존비율(%)']].rename(
    index={'female': '여성', 'male': '남성'}
).to_string())
print()

# 바차트 그리기
labels = ['남성 (Male)', '여성 (Female)']
male_rate = survival_by_sex.loc['male', '생존비율(%)']
female_rate = survival_by_sex.loc['female', '생존비율(%)']
values = [male_rate, female_rate]
colors = ['steelblue', 'lightcoral']

fig, ax = plt.subplots(figsize=(7, 6))
bars = ax.bar(labels, values, color=colors, width=0.5, edgecolor='black', linewidth=0.8)

# 막대 위에 수치 표시
for bar, val in zip(bars, values):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 0.8,
        f'{val:.1f}%',
        ha='center', va='bottom',
        fontsize=14, fontweight='bold'
    )

ax.set_title('타이타닉 - 성별 생존 비율', fontsize=16, fontweight='bold', pad=15)
ax.set_ylabel('생존 비율 (%)', fontsize=12)
ax.set_ylim(0, 100)
ax.axhline(y=50, color='gray', linestyle='--', linewidth=0.8, alpha=0.7)
ax.grid(axis='y', linestyle='--', alpha=0.4)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# 범례 (전체 인원 / 생존자수 표시)
male_total = int(survival_by_sex.loc['male', '전체인원'])
male_survived = int(survival_by_sex.loc['male', '생존자수'])
female_total = int(survival_by_sex.loc['female', '전체인원'])
female_survived = int(survival_by_sex.loc['female', '생존자수'])

info_text = (
    f"남성: {male_survived}/{male_total}명 생존\n"
    f"여성: {female_survived}/{female_total}명 생존"
)
ax.text(0.98, 0.05, info_text, transform=ax.transAxes,
        fontsize=10, va='bottom', ha='right',
        bbox=dict(boxstyle='round,pad=0.4', facecolor='lightyellow', alpha=0.8))

plt.tight_layout()
plt.savefig('titanic_survival_by_sex.png', dpi=150, bbox_inches='tight')
print("차트 저장 완료: titanic_survival_by_sex.png")
plt.show()
