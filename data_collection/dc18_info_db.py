#%% 
from dataclasses import dataclass, asdict, field, fields
from datetime import datetime
import pandas as pd
import os
from trader.tools.tools import get_df_krx

df_krx = get_df_krx()

@dataclass
class StockInfo: 
    code: str 
    name: str = "" 
    GPT_response: str = "" 
    industry: str = "" 
    business_model: str = "" 
    products: str = "" 
    competitors: str = "" 
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

class Info_DB:
    cd_ = os.path.dirname(os.path.abspath(__file__))
    filename = 'info_db.xlsx'
    designated_dir = 'CCA'
    db_path = os.path.join(cd_, designated_dir, filename)

    def __init__(self):
        self.load_from_disk()
    
    def load_from_disk(self):
        if os.path.exists(Info_DB.db_path):
            self.db = pd.read_excel(Info_DB.db_path, index_col="code", engine='openpyxl', dtype={'code':str})
        else:
            self.db = pd.DataFrame(columns=[f.name for f in fields(StockInfo)])
            self.db.set_index("code", inplace=True)
        self.db = self.db.fillna("").astype(str)

    def save_to_disk(self):
        self.db.to_excel(Info_DB.db_path, engine='openpyxl')

    def add_company(self, s: StockInfo):
        s.name = df_krx.loc[s.code, "Name"]
        s.updated = datetime.now().strftime("%Y-%m-%d")
        self.db.loc[s.code] = asdict(s)

    def read_company(self, code: str) -> StockInfo:
        if code in self.db.index:
            row_dict = self.db.loc[code].to_dict()
            row_dict['code'] = code
            return StockInfo(**row_dict)
        else: 
            return StockInfo(code)

def get_company_issues(code):
    idb = Info_DB()
    s = idb.read_company(code)
    issues = s.get_issues()
    prev = s.GPT_response
    date_updated = s.updated
    return issues, prev, date_updated

def save_GPT_response(code, response):
    idb = Info_DB()
    s = idb.read_company(code)
    s.GPT_response = response
    idb.add_company(s) # date_updated updated
    idb.save_to_disk()
