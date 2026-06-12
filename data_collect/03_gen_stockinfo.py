#%%
import pandas as pd
import os
from datetime import datetime
from dataclasses import dataclass, asdict, field, fields
from abc import ABC

cd_ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # ..
stockinfo_db_file = os.path.join(cd_, 'data/stockinfo_db.feather')
stockissue_db_file = os.path.join(cd_, 'data/stockissue_db.feather')

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

class InfoDB(ABC):
    data_class = None  # must be overridden
    def __init__(self, db_filename):
        self.filename = db_filename
        if os.path.exists(db_filename):
            self.db = pd.read_feather(db_filename)
        else:
            self.db = pd.DataFrame(
                columns=[f.name for f in fields(self.data_class)]
            )
            self.db.set_index("code", inplace=True)

    def save_to_disk(self):
        self.db.to_feather(self.filename)

    def add(self, obj):
        self.db.loc[obj.code] = asdict(obj)

    def get(self, code):
        if code in self.db.index:
            row = self.db.loc[code].to_dict()
            row["code"] = code
            return self.data_class(**row)
        return self.data_class(code)

class StockInfoDB(InfoDB):
    data_class = StockInfo
    def __init__(self, db_filename=stockinfo_db_file):
        super().__init__(db_filename)

class StockIssueDB(InfoDB):
    data_class = StockIssue
    def __init__(self, db_filename=stockissue_db_file):
        super().__init__(db_filename)