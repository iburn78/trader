#%% 
from dataclasses import dataclass, asdict, field, fields
from datetime import datetime
import pandas as pd
import os


@dataclass
class StockInfo: 
    code: str 
    name: str = None 
    GPT_response: str = None 
    industry: str = None 
    business_model: str = None 
    products: str = None 
    competitors: str = None 
    issue1: str = None 
    issue2: str = None 
    issue3: str = None 
    issue4: str = None 
    issue5: str = None 
    note: str = None 
    updated: datetime = field(default_factory=datetime.now)

    def __str__(self):
        lines = []
        for field_ in fields(self):
            value = getattr(self, field_.name)
            if value is not None:
                if isinstance(value, datetime):
                    value = value.strftime("%Y-%m-%d %H:%M:%S")
                lines.append(f"{field_.name:<15}: {value}")
        return "\n".join(lines)

class Info_DB:
    cd_ = os.path.dirname(os.path.abspath(__file__))
    filename = 'info_db.xlsx'
    designated_dir = 'CCA'
    db_path = os.path.join(cd_, designated_dir, filename)

    def __init__(self):
        self.db = self.load()
    
    def load(self):
        if os.path.exists(Info_DB.db_path):
            info_db = pd.read_excel(Info_DB.db_path, index_col="code", engine='openpyxl')
        else:
            info_db = pd.DataFrame(columns=[f.name for f in fields(StockInfo)])
            info_db.set_index("code", inplace=True)
        return info_db

    def save(self):
        self.db.to_excel(Info_DB.db_path, engine='openpyxl')

    def add(self, info: StockInfo):
        info.updated = datetime.now()
        self.db.loc[info.code] = asdict(info)

    def read(self, code: str) -> StockInfo:
        if code in self.db.index:
            row_dict = self.db.loc[code].to_dict()
            row_dict['code'] = code
            return StockInfo(**row_dict)
        else: 
            return StockInfo(code)

if __name__ == "__main__":
    idb = Info_DB()
    # s = StockInfo(code="005931", name="Samsung Electronics", industry="Elec")
    # idb.add(s)
    # idb.save()
    # r = idb.read('005930')
    # print(r)
