import streamlit as st
import pandas as pd

# 처음에 제공해주신 이미지(image_e98258.png) 기준 최신 봉급표 (5급, 4급) - 31호봉까지
salary_table = {
    5: [0, 2162100, 2195700, 2233800, 2276600, 2331700, 2412900, 2519600, 2622400, 2720300, 
        2813000, 2902700, 2990300, 3074500, 3155100, 3232400, 3307100, 3376800, 3444300, 
        3509300, 3571100, 3630200, 3686900, 3740800, 3792900, 3842300, 3890300, 3930200, 
        3968700, 4005100, 4040300, 4074600],
    4: [0, 2317100, 2367900, 2423800, 2485200, 2567100, 2682600, 2798700, 2915800, 3027100, 
        3133300, 3233400, 3331900, 3425300, 3514500, 3599900, 3680600, 3758100, 3832100, 
        3902000, 3968400, 4031800, 4091600, 4149600, 4204500, 4256500, 4306500, 4348700, 
        4388000, 4426100, 4462400, 4496500]
}

def get_base_salary(grade, step):
    # 호봉표 상한(31호봉) 처리
    if step > 31: step = 31
    return salary_table[grade][step]

def get_long_term_allowance(years):
    # 장기근속수당 (정근수당가산금)
    if years < 5: return 30000
    elif 5 <= years < 10: return 50000
    elif 10 <= years < 15: return 60000
    elif 15 <= years < 20: return 80000
    else: return 100000

def calculate_salary(start_year, current_age, start_step, military_years, retirement_age, increase_rate):
    years_to_work = retirement_age - current_age
    total_service_years = military_years
    
    current_grade = 5
    current_step = start_step
    
    data = []
    
    for i in range(years_to_work + 1):
        year = start_year + i
        age = current_age + i
        
        # 입사 후 8년 경과(9년차) 시 4급 자동 승진 및 1호봉 삭감
        if i == 8:
            current_grade = 4
            current_step -= 1
        
        # 1. 호봉표에 따른 해당 연도의 기본급 산출
        base_salary_from_table = get_base_salary(current_grade, current_step)
        
        # 2. 사용자가 설정한 연평균 기본급 인상률을 복리로 적용
        # i가 0(첫 해)일 때는 인상률 미적용, 1년 지날 때마다 설정한 %만큼 누적 인상됨
        adjusted_base_salary = int(base_salary_from_table * ((1 + increase_rate / 100) ** i))
        
        # --- 매월 고정 수당 ---
        meal_allowance = 220000  # 정액급식비 22만원
        grade_subsidy = 125000 if current_grade == 5 else 140000
        long_term_allowance = get_long_term_allowance(total_service_years)
        
        monthly_fixed = adjusted_base_salary + meal_allowance + grade_subsidy + long_term_allowance
        
        # --- 연간 상여 및 변동 수당 ---
        # 1. 명절휴가비: 인상된 기본급의 80% x 2회
        holiday_allowance = adjusted_base_salary * 0.8 * 2
        
        # 2. 정근수당: 인상된 기본급 기준 1년당 5%씩 증가(최대 50%) x 2회
        junggeun_rate = min(max(total_service_years, 0) * 0.05, 0.5)
        junggeun_allowance = adjusted_base_salary * junggeun_rate * 2
        
        # 3. 정기상여금: 인상된 기본급의 50% x 2회
        regular_bonus = adjusted_base_salary * 0.5 * 2
        
        # 4. 대민업무지원비 (3월: 30%+45.5만, 7월: 64%, 10월: 100만)
        public_support = (adjusted_base_salary * 0.3 + 455000) + (adjusted_base_salary * 0.64) + 1000000
        
        annual_bonuses = holiday_allowance + junggeun_allowance + regular_bonus + public_support
        
        # 총 연봉
        total_annual_salary = (monthly_fixed * 12) + annual_bonuses
        
        data.append({
            "연도": f"{year}년",
            "나이": f"{age}세",
            "재직기간": f"{total_service_years}년",
            "급수": f"{current_grade}급",
            "호봉": f"{current_step}호봉",
            "기본급(월)": f"{adjusted_base_salary:,.0f}원",
            "상여·수당 합계(연)": f"{annual_bonuses:,.0f}원",
            "추정 총 연봉": f"{total_annual_salary:,.0f}원"
        })
        
        current_step += 1
        total_service_years += 1
        
    return pd.DataFrame(data)

# --- Streamlit UI 구성 ---
st.set_page_config(page_title="사학연금 & 생애소득 시뮬레이터", layout="wide")
st.title("🏥 사학연금 및 생애소득 시뮬레이터 (최신 기준 반영)")
st.markdown("""
최신 호봉표 및 정액급식비(22만 원)가 반영되었습니다.
동기분들의 **시작 호봉**, **군소급 인정 기간**, 그리고 **예상 기본급 인상률**을 입력하여 연봉 변화를 시뮬레이션 해보세요.
*(※ 가족수당, 초과근무수당, 기타 특수업무수당 등은 제외된 기본 추정치입니다.)*
""")

with st.sidebar:
    st.header("⚙️ 기준 정보 입력")
    start_year = st.number_input("임용 연도", min_value=2000, max_value=2050, value=2024)
    current_age = st.number_input("임용 시 현재 나이", min_value=20, max_value=60, value=30)
    start_step = st.number_input("시작 호봉 (5급)", min_value=1, max_value=10, value=1)
    military_years = st.number_input("군소급 인정 기간(년)", min_value=0, max_value=5, value=0)
    retirement_age = st.number_input("희망 정년 나이", min_value=50, max_value=65, value=60)
    
    st.divider()
    st.markdown("**📈 연봉 상승 조건**")
    # 0.0부터 5.0까지 0.5 단위로 조절 가능한 슬라이더 추가
    increase_rate = st.slider("연평균 기본급 인상률 예상 (%)", min_value=0.0, max_value=5.0, value=1.5, step=0.5)
    st.caption("※ 호봉 승급에 따른 기본 인상 외에, 매년 임금협상에 따른 호봉표 자체의 인상률을 가정합니다.")
    
    calc_button = st.button("계산하기", type="primary")

if calc_button:
    df = calculate_salary(start_year, current_age, start_step, military_years, retirement_age, increase_rate)
    
    st.subheader(f"✅ {start_year}년 임용 동기 시뮬레이션 결과")
    
    # 요약 정보
    final_salary = df.iloc[-1]['추정 총 연봉']
    total_years = df.iloc[-1]['재직기간']
    
    col1, col2, col3 = st.columns(3)
    col1.info(f"**정년퇴직 시 재직기간(군소급 포함):** {total_years}")
    col2.success(f"**정년퇴직 시 추정 연봉:** {final_salary}")
    col3.warning(f"**진급 룰:** 8년 후 4급 진급 (1호봉 삭감)")
    
    # 데이터프레임 표시
    st.dataframe(df, use_container_width=True, hide_index=True)