ACCOUNT_NAME_DICTIONARY = {
    '유동자산':'liquid_assets', 
    '비유동자산':'illiquid_assets', 
    '자산총계':'assets',
    '유동부채':'liquid_debts',
    '비유동부채':'illiquid_debts',
    '부채총계':'debts',
    '자본금':'capital_stock',
    '이익잉여금':'retained_earnings',
    '자본총계':'equity',
    '매출액':'revenue',
    '영업이익':'operating_income',
    '법인세차감전 순이익':'profit_before_tax',
    '당기순이익':'net_income',
}

BS_ACCOUNTS=['유동자산','비유동자산','자산총계','유동부채','비유동부채','부채총계','자본금','이익잉여금','자본총계']
IS_ACCOUNTS=['매출액','영업이익','법인세차감전 순이익','당기순이익']

KRW_UNIT = 10**6