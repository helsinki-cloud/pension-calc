import streamlit as st
import pandas as pd

# 최신 봉급표 (5급, 4급) - 31호봉까지
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
    if step > 31: step = 31
    return salary_table[grade][step]

def get_long_term_allowance(years):
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
    final_annual_salary = 0
    
    for i in range(years_to_work + 1):
        year = start_year + i
        age = current_age + i
        
        # 8년 경과(9년차) 시 4급 승진 및 1호봉 삭감
        if i == 8:
            current_grade = 4
            current_step -= 1
        
        base_salary_from_table = get_base_salary(current_grade, current_step)
        adjusted_base_salary = int(base_salary_from_table * ((1 + increase_rate / 100) ** i))
        
        meal_allowance = 220000
        grade_subsidy = 125000 if current_grade == 5 else 140000
        long_term_allowance = get_long_term_allowance(total_service_years)
        
        monthly_fixed = adjusted_base_salary + meal_allowance + grade_subsidy + long_term_allowance
        
        holiday_allowance = adjusted_base_salary * 0.8 * 2
        junggeun_rate = min(max(total_service_years, 0) * 0.05, 0.5)
        junggeun_allowance = adjusted_base_salary * junggeun_rate * 2
        regular_bonus = adjusted_base_salary * 0.5 * 2
        public_support = (adjusted_base_salary * 0.3 + 455000) + (adjusted_base_salary * 0.64) + 1000000
        
        annual_bonuses = holiday_allowance + junggeun_allowance + regular_bonus + public_support
        
        total_annual_salary = (monthly_fixed * 12) + annual_bonuses
        final_annual_salary = total_annual_salary
        
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
        
    return pd.DataFrame(data), final_annual_salary, total_service_years - 1

st.set_page_config(page_title="생애소득 및 사학연금 시뮬레이터", layout="wide")
st.title("생애소득 및 사학연금 시뮬레이터")

with st.sidebar:
    st.header("입력 정보")
    start_year = st.number_input("임용 연도", min_value=2000, max_value=2050, value=2024)
    current_age = st.number_input("임용 시 현재 나이", min_value=20, max_value=60, value=30)
    start_step = st.number_input("시작 호봉 (5급)", min_value=1, max_value=10, value=1)
    military_years = st.number_input("군소급 인정 기간(년)", min_value=0, max_value=5, value=0)
    retirement_age = st.number_input("희망 정년 나이", min_value=50, max_value=65, value=60)
    
    st.divider()
    increase_rate = st.slider("연평균 기본급 인상률 (%)", min_value=0.0, max_value=5.0, value=1.5, step=0.5)
    
    calc_button = st.button("계산하기", type="primary", use_container_width=True)

if calc_button:
    df, final_salary, total_years = calculate_salary(start_year, current_age, start_step, military_years, retirement_age, increase_rate)
    
    # 사학연금 예상 수령액 계산 (2016년 이후 임용자 기준 지급률 1.7% 적용)
    # 산식: 최종 평균기준소득월액(추정) * 총 재직기간 * 1.7%
    estimated_monthly_pension = (final_salary / 12) * total_years * 0.017
    
    col1, col2, col3 = st.columns(3)
    col1.metric("총 재직기간 (군소급 포함)", f"{total_years}년")
    col2.metric("정년퇴직 시 추정 연봉", f"{int(final_salary):,}원")
    col3.metric("예상 사학연금 (월, 65세부터)", f"{int(estimated_monthly_pension):,}원")
    
    st.dataframe(df, use_container_width=True, hide_index=True)
