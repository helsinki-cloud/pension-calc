def calculate_salary(start_year, current_age, start_step, military_months, retirement_age, increase_rate):
    years_to_work = retirement_age - current_age
    current_grade = 5
    current_step = start_step
    
    data = []
    taxable_monthly_incomes_revalued = []
    np_monthly_incomes_revalued = []  # 국민연금 상한 적용 소득
    total_pension_contributions = 0
    total_national_pension_contributions = 0
    
    # 2026년 기준 국민연금 상한액
    NP_MAX_INCOME = 6370000 
    
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
        
        # 퇴직 시점 가치로 소득재평가
        revalued_income = standard_monthly_income * ((1 + increase_rate / 100) ** (years_to_work - i))
        taxable_monthly_incomes_revalued.append(revalued_income)
        
        # 국민연금용 소득 (상한선 제한 적용)
        np_capped_income = min(standard_monthly_income, NP_MAX_INCOME)
        np_revalued_income = np_capped_income * ((1 + increase_rate / 100) ** (years_to_work - i))
        np_monthly_incomes_revalued.append(np_revalued_income)
        
        # 사학연금 기여금 (9%)
        annual_contribution = standard_monthly_income * 0.09 * 12
        total_pension_contributions += annual_contribution
        
        # 국민연금 기여금 (개정 반영: 2026년부터 단계적 인상 반영 시 대략 평균 5%~6.5% 수준)
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
    
    # 1. 사학연금 계산 (재직 1년당 1.7%)
    avg_standard_monthly_income = sum(taxable_monthly_incomes_revalued) / len(taxable_monthly_incomes_revalued)
    estimated_gross_pension = avg_standard_monthly_income * final_service_years_float * 0.017
    
    # 2. 국민연금 정밀 표준 산식 반영 (2026년 기준)
    # A값: 전체 가입자의 최근 3년간 평균소득월액 (2026년 약 320만 원 기준)
    assumed_A_value = 3200000 
    # B값: 본인의 재평가된 평균 기준소득월액 (상한 적용)
    avg_np_monthly_income = sum(np_monthly_incomes_revalued) / len(np_monthly_incomes_revalued)
    
    # 국민연금 기본연금액 공식 (소득대체율 43% 기준 개정 산식)
    # 20년 가입 기준 기본 산식 후 20년 초과 1년당 5% 가산
    extra_years = max(0, final_service_years_float - 20)
    
    # 연 12개월 기준 월 수령액 계산
    annual_np_basic = 1.25 * 1.075 * (assumed_A_value + avg_np_monthly_income) * (1 + 0.05 * extra_years)
    national_pension_gross = (annual_np_basic / 12) * (final_service_years_float / 40)
    
    return pd.DataFrame(data), final_service_months, total_pension_contributions, total_national_pension_contributions, estimated_gross_pension, national_pension_gross
