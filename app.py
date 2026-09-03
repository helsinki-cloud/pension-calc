import streamlit as st
import pandas as pd

# 2025 단체협약 기준 (5급, 4급) - 31호봉까지
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
    if step > 31: 
        step = 31
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
            
    # [디버깅] 들여쓰기 수정: if문 밖으로 빼내어 항시 계산되도록 함
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

def calculate_salary(start_year, current_age, start_step, military_months, retirement_age, increase_rate):
    years_to_work = retirement_age - current_age
    current_grade = 5
    current_step = start_step
    
    data = []
    taxable_monthly_incomes_revalued = []
    np_monthly_incomes_revalued = []
    total_pension_contributions = 0
    total_national_pension_contributions = 0
    
    NP_MAX_INCOME = 6370000  # 국민연금 소득 상한선
    
    for i in range(years_to_work + 1):
        year = start_year + i
        age = current_age + i
        
        if i == 8:
            current_grade = 4
            current_step = max(1, current_step - 1)
            
        current_service_months = military_months + (i * 12)
        current_service_years_int = current_service_months // 12
        
        base_salary_from_table = get_base_salary(current_grade, current_step)
        adjusted_base_salary = int(base_salary_from_table * ((1 + increase_rate / 100) ** i))
        
        meal_allowance = 220000
        grade_subsidy = 125000 if current_grade == 5 else 140000
        long_term_allowance = get_long_term_allowance(current_service_years_int)
        work_research_allowance = 120000
        
        monthly_fixed = adjusted_base_salary + meal_allowance + grade_subsidy + long_term_allowance + work_research_allowance
        
        holiday_allowance = adjusted_base_salary * 0.8 * 2
        junggeun_rate = min(max(current_service_years_int, 0) * 0.05, 0.5)
        junggeun_allowance = adjusted_base_salary * junggeun_rate * 2
        regular_bonus = adjusted_base_salary * 0.5 * 2
        public_support = (adjusted_base_salary * 0.3 + 455000) + (adjusted_base_salary * 0.64) + 1000000
        
        annual_bonuses = holiday_allowance + junggeun_allowance + regular_bonus + public_support
        total_annual_salary = (monthly_fixed * 12) + annual_bonuses
        
        taxable_annual_income = total_annual_salary - (meal_allowance * 12)
        standard_monthly_income = taxable_annual_income / 12
        
        # 소득재평가 반영
        revalued_income = standard_monthly_income * ((1 + increase_rate / 100) ** (years_to_work - i))
        taxable_monthly_incomes_revalued.append(revalued_income)
        
        # 국민연금 상한 적용 소득
        np_capped_income = min(standard_monthly_income, NP_MAX_INCOME)
        np_revalued_income = np_capped_income * ((1 + increase_rate / 100) ** (years_to_work - i))
        np_monthly_incomes_revalued.append(np_revalued_income)
        
        # 기여금 계산
        annual_contribution = standard_monthly_income * 0.09 * 12
        total_pension_contributions += annual_contribution
        
        annual_np_contribution = np_capped_income * 0.045 * 12
        total_national_pension_contributions += annual_np_contribution
        
        data.append({
            "연도": f"{year}년",
            "나이": f"{age}세",
            "재직(연금산정)": f"{current_service_years_int}년 {current_service_months % 12}개월",
            "직급/호봉": f"{current_grade}급 {current_step}호봉",
            "월 기본급": f"{adjusted_base_salary:,.0f}원",
            "연간 상여/수당": f"{annual_bonuses:,.0f}원",
            "사학연금 납부액(연)": f"{annual_contribution:,.0f}원",
            "예상 총 연봉(세전)": f"{total_annual_salary:,.0f}원"
        })
        
        current_step += 1
        
    final_service_months = military_months + (years_to_work * 12)
    final_service_years_float = final_service_months / 12
    
    # 사학연금 계산 (1.7%)
    avg_standard_monthly_income = sum(taxable_monthly_incomes_revalued) / len(taxable_monthly_incomes_revalued)
    estimated_gross_pension = avg_standard_monthly_income * final_service_years_float * 0.017
    
    # 국민연금 정상 산식 적용
    assumed_A_value = 3200000 
    avg_np_monthly_income = sum(np_monthly_incomes_revalued) / len(np_monthly_incomes_revalued)
    extra_years = max(0, final_service_years_float - 20)
    
    annual_np_basic = 1.25 * 1.075 * (assumed_A_value + avg_np_monthly_income) * (1 + 0.05 * extra_years)
    national_pension_gross = (annual_np_basic / 12) * (final_service_years_float / 40)
    
    return pd.DataFrame(data), final_service_months, total_pension_contributions, total_national_pension_contributions, estimated_gross_pension, national_pension_gross

# Streamlit UI
st.set_page_config(page_title="생애소득 및 사학연금 시뮬레이터", layout="wide")
st.title("🏥 생애소득 및 사학연금 시뮬레이터")

with st.sidebar:
    st.header("👤 기본 정보")
    start_year = st.number_input("임용 연도", min_value=2000, max_value=2050, value=2024, help="입사한 연도를 입력하세요.")
    current_age = st.number_input("임용 시 나이 (만)", min_value=20, max_value=60, value=30)
    start_step = st.number_input("입사 시 시작 호봉 (5급 기준)", min_value=1, max_value=10, value=1)
    military_months = st.number_input("군소급 인정 기간 (개월)", min_value=0, max_value=60, value=0, step=1)
    retirement_age = st.number_input("정년 퇴직 나이", min_value=50, max_value=65, value=60)
    
    st.divider()
    
    st.header("📈 경제 지표 가정")
    increase_rate = st.slider("연평균 기본급 인상률 (%)", min_value=0.0, max_value=5.0, value=1.5, step=0.5)
    inflation_rate = st.slider("연평균 물가상승률 (%)", min_value=0.0, max_value=5.0, value=2.0, step=0.5)
    
    calc_button = st.button("계산하기", type="primary", use_container_width=True)

if calc_button:
    df, final_service_months, total_contributions, total_np_contributions, estimated_gross_pension, np_gross_pension = calculate_salary(
        start_year, current_age, start_step, military_months, retirement_age, increase_rate
    )
    
    monthly_tax, estimated_net_pension = calculate_pension_tax(estimated_gross_pension)
    
    # [디버깅] ZeroDivisionError 방지
    recovery_years = total_contributions / (estimated_net_pension * 12) if estimated_net_pension > 0 else 0
    
    years_to_pension = max(0, 65 - current_age)
    pv_net_pension = estimated_net_pension / ((1 + inflation_rate / 100) ** years_to_pension)
    
    np_monthly_tax, np_net_pension = calculate_pension_tax(np_gross_pension)
    np_pv_net_pension = np_net_pension / ((1 + inflation_rate / 100) ** years_to_pension)
    
    st.markdown("### 📊 재직 및 연금납부 요약 (사학연금 기준)")
    col_a, col_b, col_c = st.columns(3)
    col_a.metric(label="총 재직기간 (군소급 포함)", value=f"{final_service_months // 12}년 {final_service_months % 12}개월")
    col_b.metric(label="납부한 사학연금 기여금 총액", value=f"{int(total_contributions):,}원")
    col_c.metric(label="사학연금 기여금 회수 기간", value=f"{recovery_years:.1f}년")
    
    st.divider()
    
    st.markdown("### 💰 65세 예상 사학연금 (월 수령액)")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(label="① 세전 수령액", value=f"{int(estimated_gross_pension):,}원")
    col2.metric(label="② 세금 (소득/지방세)", value=f"{int(monthly_tax):,}원")
    col3.metric(label="③ 세후 수령액", value=f"{int(estimated_net_pension):,}원")
    col4.metric(label="④ 현재 가치 환산", value=f"{int(pv_net_pension):,}원")

    st.divider()

    st.markdown("### ⚖️ 국민연금 가입 시 비교 (동일 소득 기준 간이 비교)")
    col_n1, col_n2, col_n3, col_n4 = st.columns(4)
    col_n1.metric(label="① 국민연금 세전 수령액", value=f"{int(np_gross_pension):,}원")
    col_n2.metric(label="② 국민연금 세금", value=f"{int(np_monthly_tax):,}원")
    col_n3.metric(label="③ 국민연금 세후 수령액", value=f"{int(np_net_pension):,}원")
    col_n4.metric(label="④ 국민연금 현재 가치 환산", value=f"{int(np_pv_net_pension):,}원")

    st.markdown("---")
    st.markdown("### 🗓️ 연도별 생애소득 시뮬레이션")
    st.dataframe(df, use_container_width=True, hide_index=True)
