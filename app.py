import streamlit as st
import pandas as pd

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

def calculate_pension_tax(monthly_pension):
    yearly_pension = monthly_pension * 12
    
    if yearly_pension <= 3500000:
        deduction = yearly_pension
    elif yearly_pension <= 7000000:
        deduction = 3500000 + (yearly_pension - 3500000) * 0.4
    elif yearly_pension <= 14000000:
        deduction = 4900000 + (yearly_pension - 7000000) * 0.2
    else:
        deduction = 6300000 + (yearly_pension - 14000000) * 0.1
        if deduction > 9000000:
            deduction = 9000000
            
    income_amount = yearly_pension - deduction
    
    tax_base = income_amount - 1500000
    if tax_base < 0: tax_base = 0
    
    if tax_base <= 14000000:
        tax = tax_base * 0.06
    elif tax_base <= 50000000:
        tax = 840000 + (tax_base - 14000000) * 0.15
    elif tax_base <= 88000000:
        tax = 6240000 + (tax_base - 50000000) * 0.24
    else:
        tax = 15360000 + (tax_base - 88000000) * 0.35
        
    local_tax = tax * 0.1
    total_tax = tax + local_tax
    net_yearly = yearly_pension - total_tax
    
    return total_tax / 12, net_yearly / 12

def calculate_salary(start_year, current_age, start_step, military_years, retirement_age, increase_rate):
    years_to_work = retirement_age - current_age
    total_service_years = military_years
    
    current_grade = 5
    current_step = start_step
    
    data = []
    taxable_monthly_incomes = []
    total_pension_contributions = 0
    
    for i in range(years_to_work + 1):
        year = start_year + i
        age = current_age + i
        
        if i == 8:
            current_grade = 4
            current_step -= 1
        
        base_salary_from_table = get_base_salary(current_grade, current_step)
        adjusted_base_salary = int(base_salary_from_table * ((1 + increase_rate / 100) ** i))
        
        meal_allowance = 220000
        grade_subsidy = 125000 if current_grade == 5 else 140000
        long_term_allowance = get_long_term_allowance(total_service_years)
        work_research_allowance = 120000
        
        monthly_fixed = adjusted_base_salary + meal_allowance + grade_subsidy + long_term_allowance + work_research_allowance
        
        holiday_allowance = adjusted_base_salary * 0.8 * 2
        junggeun_rate = min(max(total_service_years, 0) * 0.05, 0.5)
        junggeun_allowance = adjusted_base_salary * junggeun_rate * 2
        regular_bonus = adjusted_base_salary * 0.5 * 2
        public_support = (adjusted_base_salary * 0.3 + 455000) + (adjusted_base_salary * 0.64) + 1000000
        
        annual_bonuses = holiday_allowance + junggeun_allowance + regular_bonus + public_support
        total_annual_salary = (monthly_fixed * 12) + annual_bonuses
        
        taxable_annual_income = total_annual_salary - (meal_allowance * 12)
        standard_monthly_income = taxable_annual_income / 12
        taxable_monthly_incomes.append(standard_monthly_income)
        
        annual_contribution = standard_monthly_income * 0.09 * 12
        total_pension_contributions += annual_contribution
        
        data.append({
            "연도": f"{year}",
            "나이": f"{age}",
            "재직기간": f"{total_service_years}년",
            "급수": f"{current_grade}급",
            "호봉": f"{current_step}호봉",
            "기본급(월)": f"{adjusted_base_salary:,.0f}",
            "상여·수당 합계(연)": f"{annual_bonuses:,.0f}",
            "연금 납부액(연)": f"{annual_contribution:,.0f}",
            "추정 총 연봉": f"{total_annual_salary:,.0f}"
        })
        
        current_step += 1
        total_service_years += 1
        
    avg_standard_monthly_income = sum(taxable_monthly_incomes) / len(taxable_monthly_incomes)
    estimated_gross_pension = avg_standard_monthly_income * (total_service_years - 1) * 0.017
    
    return pd.DataFrame(data), total_service_years - 1, total_pension_contributions, estimated_gross_pension

st.set_page_config(page_title="생애소득 및 사학연금 시뮬레이터", layout="wide")

with st.sidebar:
    start_year = st.number_input("임용 연도", min_value=2000, max_value=2050, value=2024)
    current_age = st.number_input("임용 시 현재 나이", min_value=20, max_value=60, value=30)
    start_step = st.number_input("시작 호봉 (5급)", min_value=1, max_value=10, value=1)
    military_years = st.number_input("군소급 인정 기간(년)", min_value=0, max_value=5, value=0)
    retirement_age = st.number_input("희망 정년 나이", min_value=50, max_value=65, value=60)
    st.divider()
    increase_rate = st.slider("연평균 기본급 인상률 (%)", min_value=0.0, max_value=5.0, value=1.5, step=0.5)
    inflation_rate = st.slider("연평균 물가상승률 (%) - 한국은행 목표치 기준", min_value=0.0, max_value=5.0, value=2.0, step=0.5)
    calc_button = st.button("계산하기", type="primary", use_container_width=True)

if calc_button:
    df, total_years, total_contributions, estimated_gross_pension = calculate_salary(
        start_year, current_age, start_step, military_years, retirement_age, increase_rate
    )
    
    monthly_tax, estimated_net_pension = calculate_pension_tax(estimated_gross_pension)
    recovery_years = total_contributions / (estimated_net_pension * 12)
    
    years_to_pension = 65 - current_age
    pv_net_pension = estimated_net_pension / ((1 + inflation_rate / 100) ** years_to_pension)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("납부한 사학연금 총액", f"{int(total_contributions):,}원")
    col2.metric("예상 사학연금 (세후)", f"{int(estimated_net_pension):,}원/월")
    col3.metric("본인 기여금 회수 기간", f"{recovery_years:.1f}년")
    
    st.divider()
    
    col4, col5, col6 = st.columns(3)
    col4.metric("원천징수 세금 (소득세+지방세)", f"{int(monthly_tax):,}원/월")
    col5.metric(f"현재 가치 환산 (물가상승 {inflation_rate}% 반영)", f"{int(pv_net_pension):,}원/월")
    col6.metric("총 재직기간 (군소급 포함)", f"{total_years}년")
    
    st.dataframe(df, use_container_width=True, hide_index=True)
