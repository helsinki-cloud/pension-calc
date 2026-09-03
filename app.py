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
    
    # 1. 연금소득공제
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
    
    # 2. 본인 기본 종합소득공제 (150만원)
    tax_base = income_amount - 1500000
    if tax_base < 0: tax_base = 0
    
    # 3. 소득세 산출
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
        
        # 8년 경과(9년차) 시 4급 승진 및 1호봉 삭감
        if i == 8:
            current_grade = 4
            current_step -= 1
        
        # 복리 인상률 적용
        base_salary_from_table = get_base_salary(current_grade, current_step)
        adjusted_base_salary = int(base_salary_from_table * ((1 + increase_rate / 100) ** i))
        
        # 고정 수당
        meal_allowance = 220000
        grade_subsidy = 125000 if current_grade == 5 else 140000
        long_term_allowance = get_long_term_allowance(total_service_years)
        work_research_allowance = 120000
        
        monthly_fixed = adjusted_base_salary + meal_allowance + grade_subsidy + long_term_allowance + work_research_allowance
        
        # 연동 상여/수당
        holiday_allowance = adjusted_base_salary * 0.8 * 2
        junggeun_rate = min(max(total_service_years, 0) * 0.05, 0.5)
        junggeun_allowance = adjusted_base_salary * junggeun_rate * 2
        regular_bonus = adjusted_base_salary * 0.5 * 2
        public_support = (adjusted_base_salary * 0.3 + 455000) + (adjusted_base_salary * 0.64) + 1000000
        
        annual_bonuses = holiday_allowance + junggeun_allowance + regular_bonus + public_support
        total_annual_salary = (monthly_fixed * 12) + annual_bonuses
        
        # 사학연금 부담금 (비과세인 정액급식비 제외)
        taxable_annual_income = total_annual_salary - (meal_allowance * 12)
        standard_monthly_income = taxable_annual_income / 12
        taxable_monthly_incomes.append(standard_monthly_income)
        
        annual_contribution = standard_monthly_income * 0.09 * 12
        total_pension_contributions += annual_contribution
        
        data.append({
            "연도": f"{year}년",
            "나이": f"{age}세",
            "연금산정 재직기간": f"{total_service_years}년",
            "직급/호봉": f"{current_grade}급 {current_step}호봉",
            "월 기본급": f"{adjusted_base_salary:,.0f}원",
            "연간 상여 및 수당": f"{annual_bonuses:,.0f}원",
            "납부할 연금액(연)": f"{annual_contribution:,.0f}원",
            "예상 총 연봉(세전)": f"{total_annual_salary:,.0f}원"
        })
        
        current_step += 1
        total_service_years += 1
        
    avg_standard_monthly_income = sum(taxable_monthly_incomes) / len(taxable_monthly_incomes)
    # 2016년 개정 연금법 산식 반영 (재직 1년당 1.7%)
    estimated_gross_pension = avg_standard_monthly_income * (total_service_years - 1) * 0.017
    
    return pd.DataFrame(data), total_service_years - 1, total_pension_contributions, estimated_gross_pension

st.set_page_config(page_title="생애소득 및 사학연금 시뮬레이터", layout="wide")
st.title("🏥 생애소득 및 사학연금 시뮬레이터")

with st.sidebar:
    st.header("👤 나의 기본 정보")
    start_year = st.number_input("임용 연도", min_value=2000, max_value=2050, value=2024, help="입사한 연도를 입력하세요.")
    current_age = st.number_input("임용 시 나이 (만)", min_value=20, max_value=60, value=30)
    start_step = st.number_input("입사 시 시작 호봉 (5급 기준)", min_value=1, max_value=10, value=1)
    military_years = st.number_input("군소급 인정 기간 (년)", min_value=0, max_value=5, value=0, help="소급 납부한 군 복무 기간만큼 연금 산정 재직기간에 더해집니다.")
    retirement_age = st.number_input("정년 퇴직 나이", min_value=50, max_value=65, value=60)
    
    st.divider()
    
    st.header("📈 경제 지표 가정")
    increase_rate = st.slider("연평균 기본급 인상률 (%)", min_value=0.0, max_value=5.0, value=1.5, step=0.5, help="매년 임금협상으로 오르는 기본급 자체의 인상률(물가인상분 등)을 가정합니다.")
    inflation_rate = st.slider("연평균 물가상승률 (%)", min_value=0.0, max_value=5.0, value=2.0, step=0.5, help="나중에 받을 연금을 현재 물가(돈 가치)로 환산해서 보기 위한 수치입니다.")
    
    calc_button = st.button("결과 보기", type="primary", use_container_width=True)

if calc_button:
    df, total_years, total_contributions, estimated_gross_pension = calculate_salary(
        start_year, current_age, start_step, military_years, retirement_age, increase_rate
    )
    
    monthly_tax, estimated_net_pension = calculate_pension_tax(estimated_gross_pension)
    # 원금 회수 기간 계산
    recovery_years = total_contributions / (estimated_net_pension * 12)
    
    # 65세 수령 시점의 연금 현재 가치 계산 (물가상승률 복리 할인)
    years_to_pension = 65 - current_age
    pv_net_pension = estimated_net_pension / ((1 + inflation_rate / 100) ** years_to_pension)
    
    st.markdown("### 📊 연금 및 소득 요약 (65세 수령 기준)")
    
    col1, col2, col3 = st.columns(3)
    col1.metric(label="총 재직기간 (군소급 포함)", value=f"{total_years}년", help="사학연금 산정의 기준이 되는 총 재직 연수입니다.")
    col2.metric(label="납부한 사학연금 총액", value=f"{int(total_contributions):,}원", help="재직 기간 동안 내 월급에서 공제된 사학연금 기여금의 총합입니다.")
    col3.metric(label="본인 기여금 회수 기간", value=f"{recovery_years:.1f}년", help="세후 연금 수령액 기준으로, 내가 낸 돈(기여금)을 전액 회수하는 데 걸리는 시간입니다.")
    
    st.divider()
    
    col4, col5, col6 = st.columns(3)
    col4.metric(label="예상 사학연금 (세후 수령액)", value=f"{int(estimated_net_pension):,}원 / 월", help="65세부터 통장에 찍히는 실제 수령액입니다. (소득세/지방세 공제 후)")
    col5.metric(label="원천징수 세금 (소득/지방세)", value=f"{int(monthly_tax):,}원 / 월", help="연금 수령 시 발생하는 세금(월 기준)입니다.")
    col6.metric(label=f"연금액의 현재 가치 환산", value=f"{int(pv_net_pension):,}원 / 월", help=f"물가상승률 {inflation_rate}%를 반영했을 때, 미래에 받을 연금이 지금의 돈 가치로 얼마인지 나타냅니다.")

    st.markdown("---")
    st.markdown("### 🗓️ 연도별 생애소득 시뮬레이션")
    st.caption("※ 초과근무수당, 가족수당 등 개인별로 다른 수당은 제외된 기본 추정치입니다. (비과세인 정액급식비는 연금 산정 기준액에서 제외됨)")
    st.dataframe(df, use_container_width=True, hide_index=True)
