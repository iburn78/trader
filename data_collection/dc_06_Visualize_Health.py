import sys, os
sys.path.append(os.path.dirname(os.getcwd()))  
from tools.tools import *
import pandas as pd

db = pd.read_feather('data/financial_reports_main.feather')
code = '005930'
path = 'plots/'+code+'.png'
plot_company_financial_summary(db, code, path)


