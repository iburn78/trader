
import pandas as pd
import os
from dataclasses import dataclass, asdict, field, fields

pd_ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # ..
info_db_file = os.path.join(pd_, 'data_collect/data/info_db.xlsx')

@dataclass
class StockInfo: 
    code: str 
    name: str = "" 
    LLM_response: str = "" 
    exec_summary: str = ""
    industry: str = "" 
    industry_growth: str = ""
    value_chain: str = ""
    business_model: str = "" 
    products: str = "" 
    competitors: str = "" 
    competitive_advanteges: str = ""
    valuation: str = ""
    event: str = ""
    momentum: str = ""
    issue1: str = "" 
    issue2: str = "" 
    issue3: str = "" 
    issue4: str = "" 
    issue5: str = "" 
    note: str = "" 
    updated: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))

    def __str__(self):
        lines = []
        for field_ in fields(self):
            value = getattr(self, field_.name)
            if value is not None:
                if isinstance(value, datetime):
                    value = value.strftime("%Y-%m-%d %H:%M:%S")
                lines.append(f"{field_.name:<15}: {value}")
        return "\n".join(lines)

    def get_issues(self) -> str:
        issues = [self.issue1, self.issue2, self.issue3, self.issue4, self.issue5]
        return "\n".join(issue for issue in issues if issue)

class StockInfoDB:
    def __init__(self):
        self.load_from_disk()
    
    def load_from_disk(self):
        if os.path.exists(info_db_file):
            self.db = pd.read_excel(info_db_file, index_col="code", engine='openpyxl', dtype={'code':str})
        else:
            self.db = pd.DataFrame(columns=[f.name for f in fields(StockInfo)])
            self.db.set_index("code", inplace=True)
        self.db = self.db.fillna("").astype(str)

    def save_to_disk(self):
        self.db.to_excel(info_db_file, engine='openpyxl')

    def add_company(self, s: StockInfo):
        s.name = df_krx.loc[s.code, "Name"]
        s.updated = datetime.now().strftime("%Y-%m-%d")
        self.db.loc[s.code] = asdict(s)

    def get_stockinfo(self, code: str) -> StockInfo:
        if code in self.db.index:
            row_dict = self.db.loc[code].to_dict()
            row_dict['code'] = code
            return StockInfo(**row_dict)
        else: 
            return StockInfo(code)

def get_prev_response_and_issues(code):
    idb = StockInfoDB()
    s = idb.get_stockinfo(code)
    issues = s.get_issues()
    prev_response = s.LLM_response
    date_updated = s.updated
    return issues, prev_response, date_updated

def save_LLM_response(code, response):
    idb = StockInfoDB()
    s = idb.get_stockinfo(code)
    s.LLM_response = response
    idb.add_company(s) # date_updated updated
    idb.save_to_disk()
