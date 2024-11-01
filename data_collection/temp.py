#%%
import OpenDartReader 
import sys, os
sys.path.append(os.path.dirname(os.getcwd()))  
from tools.dictionary import ACCOUNT_NAME_DICTIONARY, BS_ACCOUNTS, IS_ACCOUNTS, DART_APIS, MODIFIED_REPORT
from tools.tools import * # merge_update, generate_krx_data, log_print
import pandas as pd
import numpy as np
import datetime, time
import warnings



# %%
