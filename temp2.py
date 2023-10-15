# import sys, os
# sys.path.append(os.path.dirname(os.getcwd()))  
# print((os.getcwd()))
import pandas as pd
from tools.tools import *

db1 = pd.read_feather('data_collection/data/financial_reports_upto_2023-10-06_part1.feather')
code = '373220'
# code = '005930'

path = 'data_collection/plots/'+code+'.png'
plot_company_financial_summary(db1, code, path)