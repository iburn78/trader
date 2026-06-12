#%%
import pandas as pd
import os
from datetime import datetime
from dataclasses import dataclass, asdict, field, fields

pd_ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # ..
stockinfo_df_path = os.path.join(pd_, 'data_collect/data/stockinfo_df.feather')
stockissue_df_path = os.path.join(pd_, 'data_collect/data/stockissue_df.feather')

@dataclass
class StockInfo: 
    code: str 
    name: str = "" 
    exec_summary: str = ""
    sector: str = "" 
    sector_view: str = ""
    value_chain: str = ""
    business_model: str = "" 
    products: str = "" 
    competitors: str = "" 
    comp_advantege: str = ""
    valuation: str = ""
    momentum: str = ""
    updated: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))

    def __str__(self):
        lines = []
        for field_ in fields(self):
            value = getattr(self, field_.name)
            lines.append(f"{field_.name:<14}: {value}")
        return "\n".join(lines)

@dataclass
class StockIssue:
    code: str
    content: str = ""
    created: str = field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d'))
    resolved: bool = False

    def __str__(self):
        lines = []
        for field_ in fields(self):
            value = getattr(self, field_.name)
            lines.append(f"{field_.name:<14}: {value}")
        return "\n".join(lines)



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
