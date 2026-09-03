import streamlit as st
import pandas as pd

# ============================================================
# 2025년 단체협약(전남대병원 급여계산기 원본) 기준 봉급표 - 31호봉까지
# ============================================================
salary_table = {
    5: [0, 2162100, 2195700, 2233800, 2276600, 2331700, 2412900, 2519600, 2622400, 2720300,
        2813000, 2902700, 2990300, 3074500, 3155100, 3232400, 3307100, 3376800, 3444300,
        3509300, 3571100, 3630200, 3686900, 3740800, 3792900, 3842300, 3890300, 3930200,
        3968700, 4005100, 4040300, 4074600],
    4: [0, 2317100, 2367900, 2423800, 2485200, 2567100, 2682600, 2798700, 2915800, 3027100,
        3133300, 3233400, 3331900, 3425300, 3514500, 3599900, 3680600, 3758100, 3832100,
        3902000, 3968400, 4031800, 4091600, 4149600, 4204500, 4256500, 4306500, 4348700,
        4388000, 4426100, 4462400, 4496500],
}


def get_base_salary(grade, step):
    step = min(step, 31)
    return salary_table[grade][step]


def get_long_term_allowance(years):
    """장기근속수당(정근수당가산금)"""
    if years < 5:
        return 30000
    elif years < 10:
        return 50000
    elif years < 15:
        return 60000
    elif years < 20:
        return 80000
    else:
        return 100000


def get_grade_bonus_allowance(base_salary, grade, grade_tenure_years):
    """직급대우수당: 해당 직급 5년 이상 재직 시 지급. 4급은 11년/16년 이상 구간에서 요율 상승.
    ※ 원본 급여계산기 산식을 그대로 따랐습니다. 5급도 5년 이상이면 4.1%가 붙는 구조인데,
      규정상 4급 이상에만 적용되는 것인지는 병원 인사팀 확인이 필요합니다."""
    if grade_tenure_years < 5:
        return 0
    if grade == 4 and grade_tenure_years >= 16:
        return base_salary * 0.06
    if grade == 4 and grade_tenure_years >= 11:
        return base_salary * 0.05
    return base_salary * 0.041


def get_family_allowance(has_spouse, num_children, num_other_dependents):
    """가족수당"""
    amount = 40000 if has_spouse else 0
    if num_children == 1:
        amount += 30000
    elif num_children == 2:
        amount += 100000
    elif num_children >= 3:
        amount += 100000 + (num_children - 2) * 110000
    amount += min(num_other_dependents, 4) * 20000
    return amount


def calculate_pension_tax(monthly_pension):
    """공적연금소득세 (연금소득공제 → 종합소득세 누진세율 → 지방소득세 10%).
    본인 인적공제(150만원)만 반영한 근사치입니다. 배우자·부양가족 추가공제,
    65세 이상 경로우대공제(100만원)는 미반영되어 실제보다 세금이 다소 높게(=순연금이 다소
    적게) 계산될 수 있습니다."""
    yearly_pension = monthly_pension * 12

    if yearly_pension <= 3500000:
        deduction = yearly_pension
    elif yearly_pension <= 7000000:
        deduction = 3500000 + (yearly_pension - 3500000) * 0.4
    elif yearly_pension <= 14000000:
        deduction = 4900000 + (yearly_pension - 7000000) * 0.2
    else:
        deduction = 6300000 + (yearly_pension - 14000000) * 0.1
        deduction = min(deduction, 9000000)

    income_amount = yearly_pension - deduction
    tax_base = max(0, income_amount - 1500000)

    if tax_base <= 14000000:
        tax = tax_base * 0.06
    elif tax_base <= 50000000:
        tax = 840000 + (tax_base - 14000000) * 0.15
    elif tax_base <= 88000000:
        tax = 6240000 + (tax_base - 50000000) * 0.24
    else:
        tax = 15360000 + (tax_base - 88000000) * 0.35

    total_tax = tax * 1.1  # 지방소득세 10% 포함
    net_yearly = yearly_pension - total_tax
    return total_tax / 12, net_yearly / 12


def calculate_salary(start_year, current_age, start_step, military_months, retirement_age,
                      increase_rate, has_spouse, num_children, num_other_dependents):
    years_to_work = retirement_age - current_age
    current_grade = 5
    current_step = start_step
    grade_start_i = 0  # 현재 직급으로 승진(또는 시작)한 시점의 i

    data = []
    taxable_monthly_incomes_revalued = []
    np_monthly_incomes_revalued = []
    total_pension_contributions = 0
    total_national_pension_contributions = 0

    NP_MAX_INCOME_BASE = 6370000  # 2025년 기준 국민연금 기준소득월액 상한
    NON_TAXABLE_MEAL = 220000     # 정액급식비(비과세)

    for i in range(years_to_work + 1):
        year = start_year + i

        if i == 8:  # 8년 뒤(9년차) 4급 승진, 승진 시 1호봉 감호봉
            current_grade = 4
            current_step = max(1, current_step - 1)
            grade_start_i = i

        current_service_months = military_months + (i * 12)
        current_service_years_int = current_service_months // 12
        grade_tenure_years = i - grade_start_i

        base_salary_from_table = get_base_salary(current_grade, current_step)
        adjusted_base_salary = int(base_salary_from_table * ((1 + increase_rate / 100) ** i))

        # ---- 월 고정수당 (원본 급여계산기 산식 그대로 복원) ----
        meal_allowance = NON_TAXABLE_MEAL
        grade_subsidy = 125000 if current_grade == 5 else 140000            # 직급보조비
        risk_allowance = 60000                                              # 위험근무수당(을종)
        admin_allowance = 50000 if current_grade <= 4 else 30000            # 행정업무수당
        work_research_allowance = 203000 if current_grade == 4 else 191000  # 업무연구수당
        medical_support_allowance = 120000 if current_grade >= 3 else 0     # 진료지원수당
        long_term_allowance = get_long_term_allowance(current_service_years_int)
        grade_bonus_allowance = get_grade_bonus_allowance(adjusted_base_salary, current_grade, grade_tenure_years)
        family_allowance = get_family_allowance(has_spouse, num_children, num_other_dependents)

        monthly_fixed = (adjusted_base_salary + meal_allowance + grade_subsidy + risk_allowance
                          + admin_allowance + work_research_allowance + medical_support_allowance
                          + long_term_allowance + grade_bonus_allowance + family_allowance)

        # ---- 연간 상여 (원본 산식: 정근수당 1·7월, 명절휴가비 2·9월, 정기상여금 4·11월, 대민업무지원비 3·7·10월) ----
        holiday_allowance = adjusted_base_salary * 0.8 * 2
        junggeun_rate = min(max(current_service_years_int, 0) * 0.05, 0.5)
        junggeun_allowance = adjusted_base_salary * junggeun_rate * 2
        regular_bonus = adjusted_base_salary * 0.5 * 2
        public_support = (adjusted_base_salary * 0.3 + 455000) + (adjusted_base_salary * 0.64) + 1000000

        annual_bonuses = holiday_allowance + junggeun_allowance + regular_bonus + public_support
        total_annual_salary = (monthly_fixed * 12) + annual_bonuses

        # ---- 사학연금 기준소득월액(비과세 정액급식비만 제외) ----
        taxable_annual_income = total_annual_salary - (meal_allowance * 12)
        standard_monthly_income = taxable_annual_income / 12

        revalued_income = standard_monthly_income * ((1 + increase_rate / 100) ** (years_to_work - i))
        taxable_monthly_incomes_revalued.append(revalued_income)

        # 국민연금 기준소득월액 상한도 같은 인상률로 함께 성장한다고 가정
        np_max_income_i = NP_MAX_INCOME_BASE * ((1 + increase_rate / 100) ** i)
        np_capped_income = min(standard_monthly_income, np_max_income_i)
        np_revalued_income = np_capped_income * ((1 + increase_rate / 100) ** (years_to_work - i))
        np_monthly_incomes_revalued.append(np_revalued_income)

        annual_contribution = standard_monthly_income * 0.09 * 12
        total_pension_contributions += annual_contribution

        annual_np_contribution = np_capped_income * 0.045 * 12
        total_national_pension_contributions += annual_np_contribution

        data.append({
            "연도": f"{year}년",
            "나이": f"{current_age + i}세",
            "재직(연금산정)": f"{current_service_years_int}년 {current_service_months % 12}개월",
            "직급/호봉": f"{current_grade}급 {current_step}호봉",
            "월 기본급": f"{adjusted_base_salary:,.0f}원",
            "월 고정지급액": f"{int(monthly_fixed):,.0f}원",
            "연간 상여/수당": f"{annual_bonuses:,.0f}원",
            "사학연금 납부액(연)": f"{annual_contribution:,.0f}원",
            "예상 총 연봉(세전)": f"{total_annual_salary:,.0f}원",
        })

        current_step += 1

    final_service_months = military_months + (years_to_work * 12)
    final_service_years_float = final_service_months / 12

    # ---- 1) 사학연금: 평균기준소득월액 × 재직연수(최대 36년) × 1.7% ----
    pension_service_years = min(36.0, final_service_years_float)
    avg_standard_monthly_income = sum(taxable_monthly_incomes_revalued) / len(taxable_monthly_incomes_revalued)
    estimated_gross_pension = avg_standard_monthly_income * pension_service_years * 0.017

    # ---- 2) 국민연금(비교용): 기본연금액 = 상수 × (A+B) × (1+0.05×20년초과연수) ----
    #     ※ 20년 이상 가입 시 이 값이 곧 지급액이며, 재직연수로 다시 나누는 절차는 없습니다.
    #        (10~20년 가입자만 20년 기준액에 재직연수/20을 곱해 비례 감액)
    #     상수 1.29는 2025년 국회 통과, 2026.1.1 시행된 소득대체율 43% 개정에 대응하는 값입니다.
    assumed_A_value = 3200000 * ((1 + increase_rate / 100) ** years_to_work)
    avg_np_monthly_income = sum(np_monthly_incomes_revalued) / len(np_monthly_incomes_revalued)

    extra_years = max(0, final_service_years_float - 20)
    monthly_np_basic = (1.29 * (assumed_A_value + avg_np_monthly_income) * (1 + 0.05 * extra_years)) / 12

    if final_service_years_float < 20:
        national_pension_gross = monthly_np_basic * (final_service_years_float / 20)
    else:
        national_pension_gross = monthly_np_basic

    return (pd.DataFrame(data), final_service_months, total_pension_contributions,
            total_national_pension_contributions, estimated_gross_pension, national_pension_gross)


# ============================================================
# Streamlit UI
# ============================================================
st.set_page_config(page_title="생애소득 및 사학연금 시뮬레이터", layout="wide")
st.title("🏥 생애소득 및 사학연금 시뮬레이터")
st.caption("전남대병원 급여계산기 산식 기준 · 5급→4급(8년 뒤 승진, 1호봉 감호봉) 시나리오 반영")

with st.sidebar:
    st.header("👤 기본 정보")
    start_year = st.number_input("임용 연도", min_value=2000, max_value=2050, value=2026)
    current_age = st.number_input("임용 시 나이 (만)", min_value=20, max_value=60, value=31)
    start_step = st.number_input("입사 시 시작 호봉 (5급 기준)", min_value=1, max_value=10, value=3)
    military_months = st.number_input("군소급 인정 기간 (개월)", min_value=0, max_value=60, value=0, step=1)
    retirement_age = st.number_input("정년 퇴직 나이", min_value=50, max_value=65, value=60)

    st.divider()
    st.header("👪 가족 사항")
    has_spouse = st.checkbox("배우자 있음", value=False)
    num_children = st.number_input("부양 자녀 수 (명)", min_value=0, max_value=6, value=0)
    num_other_dependents = st.number_input("기타 부양가족 수 (명, 최대4)", min_value=0, max_value=4, value=0)

    st.divider()
    st.header("📈 경제 지표 가정")
    increase_rate = st.slider("연평균 기본급 인상률 (%)", min_value=0.0, max_value=5.0, value=3.0, step=0.5)
    inflation_rate = st.slider("연평균 물가상승률 (%)", min_value=0.0, max_value=5.0, value=2.0, step=0.5)

    calc_button = st.button("계산하기", type="primary", use_container_width=True)

if calc_button:
    df, final_service_months, total_contributions, total_np_contributions, estimated_gross_pension, np_gross_pension = calculate_salary(
        start_year, current_age, start_step, military_months, retirement_age, increase_rate,
        has_spouse, num_children, num_other_dependents,
    )

    monthly_tax, estimated_net_pension = calculate_pension_tax(estimated_gross_pension)
    recovery_years = total_contributions / (estimated_net_pension * 12) if estimated_net_pension > 0 else 0

    years_to_pension = max(0, 65 - current_age)
    pv_net_pension = estimated_net_pension / ((1 + inflation_rate / 100) ** years_to_pension)

    np_monthly_tax, np_net_pension = calculate_pension_tax(np_gross_pension)
    np_pv_net_pension = np_net_pension / ((1 + inflation_rate / 100) ** years_to_pension)

    st.markdown("### 📊 재직 및 연금납부 요약 (사학연금 기준)")
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("총 재직기간 (군소급 포함)", f"{final_service_months // 12}년 {final_service_months % 12}개월")
    col_b.metric("납부한 사학연금 기여금 총액", f"{int(total_contributions):,}원")
    col_c.metric("사학연금 기여금 회수 기간", f"{recovery_years:.1f}년")

    st.divider()

    st.markdown("### 💰 65세 예상 사학연금 (월 수령액)")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("① 세전 수령액", f"{int(estimated_gross_pension):,}원")
    col2.metric("② 세금 (소득/지방세)", f"{int(monthly_tax):,}원")
    col3.metric("③ 세후 수령액", f"{int(estimated_net_pension):,}원")
    col4.metric("④ 현재 가치 환산", f"{int(pv_net_pension):,}원")

    st.divider()

    st.markdown("### ⚖️ 국민연금 가입 시 비교 (동일 소득 기준 간이 비교, 실제 사학연금은 국민연금 미가입)")
    col_n1, col_n2, col_n3, col_n4 = st.columns(4)
    col_n1.metric("① 국민연금 세전 수령액", f"{int(np_gross_pension):,}원")
    col_n2.metric("② 국민연금 세금", f"{int(np_monthly_tax):,}원")
    col_n3.metric("③ 국민연금 세후 수령액", f"{int(np_net_pension):,}원")
    col_n4.metric("④ 국민연금 현재 가치 환산", f"{int(np_pv_net_pension):,}원")

    st.markdown("---")
    st.markdown("### 🗓️ 연도별 생애소득 시뮬레이션")
    st.dataframe(df, use_container_width=True, hide_index=True)

    with st.expander("⚠️ 계산 가정 및 한계 (꼭 한 번 읽어보세요)"):
        st.markdown("""
- **봉급표**: 5급·4급만 반영되어 있습니다(3급 이상 승진 없다는 가정과 일치).
- **직급대우수당**: 원본 급여계산기 산식을 그대로 따라 5급도 해당 직급 5년 이상이면 기본급의 4.1%가 붙습니다.
  규정상 4급 이상에만 적용되는 항목인지는 병원 인사팀 확인이 필요합니다 — 맞다면 승진 직전 3개 연도 연봉이 실제보다
  다소 높게 잡힌 것일 수 있습니다.
- **사학연금 지급률 1.7%**는 2035년 이후 최종 도달 예정 요율입니다. 그 이전 연도에는 조금 더 높은 과도기 요율이
  적용되므로, 이 계산은 장기적으로 약간 보수적(과소)인 추정치입니다.
- **국민연금 소득대체율상수 1.29**는 2025년 국회를 통과해 2026.1.1부터 시행되는 개정(소득대체율 43%)에 대응하는
  값으로, 2026년 이후 가입기간에만 적용됩니다. 이 시나리오처럼 2026년 신규 임용을 가정할 때는 문제없이 들어맞지만,
  이미 재직 중이며 2025년 이전 가입기간이 섞여 있다면 그 구간은 별도 계산이 필요합니다.
- **재평가율**은 국민연금공단이 매년 고시하는 전국민 평균소득 상승률 지수를 써야 하는데, 편의상 본인이 입력한
  기본급 인상률로 대체했습니다.
- **국민연금 기준소득월액 상한**은 실제 A값 상승과 정확히 같은 속도로 오른다는 보장이 없어, 같은 인상률 가정으로
  단순화했습니다.
- **사학연금 소득세**는 본인 인적공제(150만원)만 반영했고, 배우자·부양가족 추가공제, 65세 이상 경로우대공제
  (100만원)는 반영하지 않아 세후 연금이 실제보다 다소 적게 나올 수 있습니다.
- **사학연금은 국민연금과 이중가입이 불가능**합니다. 아래 국민연금 비교는 "만약 국민연금 대상자였다면"을 가정한
  참고용 수치입니다.
        """)
