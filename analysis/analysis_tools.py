#%%
import sys, os
sys.path.append(os.path.dirname(os.getcwd()))  
import FinanceDataReader as fdr
from tools.tools import set_KoreaFonts, generate_krx_data
from tools.koreainvest_module import *
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import time

def get_last_quarter(fh):
    return max([q for q in fh.columns if 'Q' in q])

def get_quarters(last_quarter, num = 5 ):
    year, quarter = last_quarter.split('_')
    year = int(year)
    quarter = int(quarter[0])  # Convert quarter from '2Q' to 2
    quarters = []
    current_year, current_quarter = year, quarter

    for _ in range(num):
        quarters.append(f"{current_year}_{current_quarter}Q")
        if current_quarter == 1:
            current_quarter = 4
            current_year -= 1
        else:
            current_quarter -= 1
    return quarters[::-1]

def get_quarter_simpler_string(quarters):
    res = []
    for q in quarters: 
        res.append(q[2:4]+'.'+q[5:6])
    return res
        
def draw_arrow(ax, sp, ep, 
            text = '', 
            line_color='white', 
            text_color='white', 
            text_offset=(0, 0),  # in pt (1/72 inch)
            text_size=14, 
            line_width=2, 
            arrowstyle='->'):
    arrowprops = dict(arrowstyle = arrowstyle, lw=line_width, facecolor= line_color, edgecolor= line_color, shrinkA=1, shrinkB=0)
    # mid_point = ((sp[0] + ep[0]) / 2, (sp[1] + ep[1]) / 2)
    mid_point = (sp[0] + (ep[0]-sp[0]) / 2, sp[1] + (ep[1]-sp[1]) / 2)  # this works even for Timestamp instances
    ax.annotate('', xy=ep, xytext=sp, arrowprops=arrowprops)
    ax.annotate(text, xy=mid_point, xytext=text_offset, textcoords='offset points', ha='center', va='bottom', fontsize=text_size, color=text_color)
    # ax.annotate(text, xy=mid_point, xytext=text_offset, textcoords='offset points', ha='center', va='bottom', fontproperties= font_prop, fontsize=text_size, color=text_color)
    return None

def draw_text(ax, pt, text, **kwargs):
    draw_arrow(ax, pt, pt, text=text, arrowstyle='->', **kwargs)

def draw_line(ax, sp, ep, **kwargs):
    draw_arrow(ax, sp = sp, ep = ep, arrowstyle='-', **kwargs)

def draw_increase(ax, sp, ep, ext = 1, pos = 0.85, **kwargs):
    (spx, spy) = sp
    (epx, epy) = ep
    draw_line(ax, sp, (epx+ext, spy), line_color='whitesmoke', line_width = 1, **kwargs)
    draw_line(ax, ep, (epx+ext, epy), line_color='whitesmoke', line_width = 1, **kwargs)
    if spy*epy > 0:
        increment = str(round((epy/spy-1)*100)) + '%'
    draw_arrow(ax, (epx+ext*pos, spy), (epx+ext*pos, epy), text=increment, line_width=2, **kwargs )
    
def pt_iqbefore(ith, quarters_list, y_values): # ith = 0, this quarter (last bar)
    # quarters_list: return value of get_quarters()
    x_idx = len(quarters_list)-ith-1
    return (x_idx, y_values[x_idx])


START_DATE = '2014-01-01'
def get_last_N_quarter_price(code, qts_back, start_date=START_DATE):
    # preparing last N quaters price data
    pr_raw = fdr.DataReader(code, start_date)['Close']
    last_date = pr_raw.index[-1]
    # Calculate the month of the current quarter
    quarter_month = ((last_date.month - 1) // 3) * 3 + 1
    # Calculate the first day of the quarter start_qts_back quarters before last_date
    start_date = pd.Timestamp(year=last_date.year, month=quarter_month, day=1) - pd.DateOffset(months=3 * qts_back)
    return pr_raw.loc[start_date:]


# adding rolling last 4 quater values
def L4_addition(fh, target_account):
    new_row = {'code':fh['code'].iloc[0], 'account':'L4_'+target_account }
    quarter_columns = [col for col in fh.columns if 'Q' in col]
    sorted_quarter_columns = sorted(quarter_columns)
    target_row = fh[fh['account']==target_account].iloc[0]

    for i in range(3, len(sorted_quarter_columns)):
        previous_4_quarters = sorted_quarter_columns[i-3:i+1]
        rolling_sum = target_row[previous_4_quarters].sum()
        new_row[sorted_quarter_columns[i]] = rolling_sum

    new_row_df = pd.DataFrame([new_row])
    return pd.concat([fh, new_row_df], ignore_index=True)

def get_shares_outstanding(code): 
    sl = fdr.StockListing('KRX')
    return sl.loc[sl['Code']==code, ['Stocks']].values[0,0]

def get_prev_quarter_in_format(quarter):
    return str(quarter-1).replace('Q','_') + 'Q'

# preparing PER 
# assumption: 
# - performace is immediately known to the market at the end of each quarter
# - for example, when calculating PER, prices (i.e., market cap) of a quarter will be devided by the sum of previous 4 quarters value of net_income

def get_PER_rolling(code, fh, qts_back):
    target_account='net_income'
    marcap = get_last_N_quarter_price(code, qts_back)*get_shares_outstanding(code)
    PER = pd.Series(index = marcap.index)
    for i in marcap.index:
        q = pd.to_datetime(i).to_period('Q')
        pq = get_prev_quarter_in_format(q)
        L4 = fh.loc[fh['account']=='L4_'+target_account, [pq]].values[0,0]
        PER[i] = marcap[i] / L4
    return PER

def get_PBR(code, fh, qts_back):
    target_account='assets'
    marcap = get_last_N_quarter_price(code, qts_back)*get_shares_outstanding(code)
    PBR = pd.Series(index = marcap.index)
    for i in marcap.index:
        q = pd.to_datetime(i).to_period('Q')
        pq = get_prev_quarter_in_format(q)
        divider = fh.loc[fh['account']==target_account, [pq]].values[0,0]
        PBR[i] = marcap[i] / divider
    return PBR

class Drawer:
    def __init__(self): 
        self.spine_color = 'lightgray'
        self.background_color = '#001f3f'  # deep dark blue
        self.figsize = (16, 9)
        self.ax_size = [0.05, 0.05, 0.9, 0.9]
        self.text_size = 18
        self.tick_text_size = 15

        set_KoreaFonts()
        plt.rcParams.update({
            'axes.edgecolor': self.spine_color,
            'axes.labelcolor': self.spine_color,
            'xtick.color': self.spine_color,
            'ytick.color': self.spine_color,
            'xtick.labelsize': self.tick_text_size,
            'ytick.labelsize': self.tick_text_size,
            'text.color': self.spine_color,
        })
    
    def _init_fig(self):
        self.fig = plt.figure(figsize=self.figsize)
        self.ax = self.fig.add_axes(self.ax_size)
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.fig.patch.set_facecolor(self.background_color)  # Figure background color
        self.ax.set_facecolor(self.background_color)

    def save_line_plot(self, data, type, subgraph, output_file):  
        self._init_fig()

        # type : price, PER, PBR
        # subgraph : quarterly, average
        if type == 'price':
            unit_text = '원'
            precision = 0
        elif type == 'PER':
            unit_text = '배수'
            precision = 2
        elif type == 'PBR': 
            unit_text = '배수'
            precision = 3
        else: 
            pass

        self.ax.text(0, 1.01, f'({unit_text})', fontsize=self.tick_text_size, color=self.spine_color, ha='left', va='bottom', transform=self.ax.transAxes)
        self.ax.text(1, 1.01, f'({data.index[-1].date()})', fontsize=self.tick_text_size, color=self.spine_color, ha='right', va='bottom', transform=self.ax.transAxes)
        self.ax.set_title(type, fontsize=self.text_size, weight='bold')
        self.ax.set_xlabel('quarters', fontsize=self.tick_text_size)

        self.ax.plot(data)
        if subgraph == 'quarterly':
            self._quarterly_average_plot(data, precision=precision)
        elif subgraph == 'average':
            self._average_plot(data, precision=precision)
        else:
            pass

        self.fig.savefig(output_file, format='png', transparent=True, bbox_inches='tight', pad_inches=0.2)
        plt.show()
        plt.close(self.fig)


    # Check if x-tick labels are overlapping
    def _check_xtick_label_overlap(self):
        labels = self.ax.get_xticklabels()
        if not labels:
            return False

        # Get the bounding boxes of the labels
        bboxes = [label.get_window_extent(renderer=self.ax.figure.canvas.get_renderer()) for label in labels]
        # Check if any bounding boxes overlap
        for i in range(len(bboxes) - 1):
            if bboxes[i].overlaps(bboxes[i + 1]):
                return True
        return False

    # Custom function to format x-axis ticks as yy.q
    def _format_quarter(x, pos=None): 
        date = mdates.num2date(x)
        year_short = date.year % 100  
        quarter = (date.month - 1) // 3 + 1
        return f'{year_short}.{quarter}'

    def _price_xtick_formatter(self, pr):
        quarters = pd.to_datetime(pr.index).to_period('Q')
        # Generate tick positions at the center of each quarter
        tick_positions = [(pd.to_datetime(str(q.start_time)) + (pd.to_datetime(str(q.end_time)) - pd.to_datetime(str(q.start_time))) / 2) for q in quarters.unique()]

        # Set tick positions and custom tick formatter
        self.ax.set_xticks(tick_positions)
        self.ax.xaxis.set_major_formatter(plt.FuncFormatter(Drawer._format_quarter))

        if self._check_xtick_label_overlap(): 
            self.ax.xaxis.set_major_locator(mdates.AutoDateLocator())  # Automatically set date ticks
            self.ax.xaxis.set_major_formatter(mdates.AutoDateFormatter(self.ax.xaxis.get_major_locator()))  # Set date formatter

    # price to be the result from the function get_last_N_quarter_price
    def _quarterly_average_plot(self, pr, precision=0):
        fontsize = self.tick_text_size
        quarters = pd.to_datetime(pr.index).to_period('Q')
        for quarter in quarters.unique():
            start = pd.to_datetime(str(quarter.start_time))
            end = pd.to_datetime(str(quarter.end_time))
            if precision == 0:
                avg_value = int(pr.loc[quarter.start_time:quarter.end_time].mean().round())  # Get the average for the quarter
            else: 
                avg_value = pr.loc[quarter.start_time:quarter.end_time].mean().round(precision)  
            self.ax.hlines(avg_value, xmin=start, xmax=end, color='orange', linewidth=2, label='quarterly average' if quarter == quarters.unique()[0] else "")
            # Display the average value above the line
            mid_point = start + (end - start) / 2  # Midpoint of the quarter
            self.ax.text(mid_point, avg_value + (avg_value * 0.01), f'{avg_value}', color='orange', ha='center', va='bottom', fontsize=fontsize)

        last_pt_color='orangered'
        self.ax.scatter(pr.index[-1], pr.iloc[-1], color=last_pt_color, edgecolor=last_pt_color, s=30)
        self.ax.text(pr.index[-1], pr.values[-1], f' {pr.values[-1].round(precision)}', ha='left', va='center', weight='bold', fontsize = fontsize, color=last_pt_color)
        # Iterate over each quarter and highlight even-numbered quarters
        for i, quarter in enumerate(quarters.unique()):
            if quarter.quarter % 2 == 0:  # Check if it is an even-numbered quarter
                start = pd.to_datetime(str(quarter.start_time))
                end = pd.to_datetime(str(quarter.end_time))
                self.ax.axvspan(start, end, facecolor='gray', alpha=0.2)  # Fill with a white box
        self._price_xtick_formatter(pr)

    def _average_plot(self, pr, precision = 0, n_sigma=1):
        fontsize = self.tick_text_size
        if precision == 0:
            avg_value = int(pr.mean().round())  # Get the average for the quarter
            std_value = int(pr.std().round())
        else: 
            avg_value = pr.mean().round(precision)  
            std_value = pr.std().round(precision)
        start = pr.index[0]
        end = pr.index[-1]
        upper_value = round(avg_value+n_sigma*std_value, precision)
        lower_value = round(avg_value-n_sigma*std_value, precision)
        self.ax.hlines(avg_value, xmin=pr.index[0], xmax=pr.index[-1], color='orange', linewidth=4)
        self.ax.hlines(upper_value, xmin=pr.index[0], xmax=pr.index[-1], color='orange', linewidth=1)
        self.ax.hlines(lower_value, xmin=pr.index[0], xmax=pr.index[-1], color='orange', linewidth=1)
        last_pt_color='orangered'
        self.ax.scatter(pr.index[-1], pr.iloc[-1], color=last_pt_color, edgecolor=last_pt_color, s=30)
        self.ax.text(pr.index[-1], pr.values[-1], f' {pr.values[-1].round(precision)}', ha='left', va='center', weight='bold', fontsize = fontsize, color=last_pt_color)
        mid_point = start + (end - start) / 2  # Midpoint of the quarter
        self.ax.text(mid_point, avg_value + (avg_value * 0.01), f'{avg_value}', color='orange', ha='center', va='bottom', fontsize=fontsize)
        self.ax.text(mid_point, upper_value + (upper_value * 0.01), f'{upper_value}', color='orange', ha='center', va='bottom', fontsize=fontsize)
        self.ax.text(mid_point, lower_value + (lower_value * 0.01), f'{lower_value}', color='orange', ha='center', va='bottom', fontsize=fontsize)
        arrow_point = int(len(pr)*3/4)
        draw_arrow(self.ax, (pr.index[arrow_point], avg_value*(1.01)), (pr.index[arrow_point], upper_value), '+1$\sigma$', text_offset=(17, 0))
        draw_arrow(self.ax, (pr.index[arrow_point], avg_value*(0.99)), (pr.index[arrow_point], lower_value), '-1$\sigma$', text_offset=(17, 0))
        self._price_xtick_formatter(pr)

#################
#################

class Broker:
    def __init__(self):
        self.broker = self.get_broker()

    def get_broker(self, mock=False):
        with open('../../config/config.json', 'r') as json_file:
            config = json.load(json_file)
            if mock:
                # key_mock = config['key_mock']
                # secret_mock = config['secret_mock']
                # acc_no_mock = config['acc_no_mock']
                # broker = KoreaInvestment(api_key=key_mock, api_secret=secret_mock, acc_no=acc_no_mock, mock=True)
                pass
            else: 
                key = config['key']
                secret = config['secret']
                acc_no = config['acc_no']
                broker = KoreaInvestment(api_key=key, api_secret=secret, acc_no=acc_no, mock=False)
        return broker

    def fetch_foreign_holdings(self, code, period): 
        # period: D, W, M
        base_url = "https://openapi.koreainvestment.com:9443"
        path = "/uapi/domestic-stock/v1/quotations/inquire-daily-price"
        url = f"{base_url}/{path}"
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": self.broker.access_token,
            "appKey": self.broker.api_key,
            "appSecret": self.broker.api_secret,
            "tr_id": "FHKST01010400",
            "tr_cont": "",
        }

        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": code,
            "FID_PERIOD_DIV_CODE":period, 
            "FID_ORG_ADJ_PRC":"0000000000" # modified stock prices
        }

        res = requests.get(url, headers=headers, params=params)
        if res.json()['rt_cd'] == '0' and len(res.json()['output']) > 0:
            res = pd.DataFrame(res.json()['output'])
        else: 
            return None

        type_casting = {'stck_clpr':'int', 'hts_frgn_ehrt':'float'}
        res = res.astype(type_casting)
        foreign_holdings = res.set_index('stck_bsop_date')[['stck_clpr', 'hts_frgn_ehrt']].sort_index()
        corr = foreign_holdings['stck_clpr'].corr(foreign_holdings['hts_frgn_ehrt'])
        foreign_holdings = foreign_holdings.reset_index().rename(columns={'stck_bsop_date':'date', 'stck_clpr':'price', 'hts_frgn_ehrt':'fh'})

        return foreign_holdings, corr

    def fetch_corr_foreign_holdings(self, code): 
        fh_d, cr_d = self.fetch_foreign_holdings(code, 'D')
        fh_w, cr_w = self.fetch_foreign_holdings(code, 'W')
        fh_m, cr_m = self.fetch_foreign_holdings(code, 'M')

        return [code, cr_d, cr_w, cr_m]


    def generate_corr_data(self):
        MARCAP_THRESHOLD = 5000*10**8 
        IPO_YEAR_THRESHOLD = 3 
        # generate_krx_data()
        df_krx = pd.read_feather('data/df_krx.feather')
        df_krx = df_krx.loc[df_krx['Marcap'] >= MARCAP_THRESHOLD]
        df_krx = df_krx.loc[pd.Timestamp.today()- df_krx['ListingDate'] > pd.Timedelta(days = IPO_YEAR_THRESHOLD*(365+1))]

        corr = []
        for code in df_krx.index:
            corr_ = self.fetch_corr_foreign_holdings(code)
            time.sleep(0.1)
            corr_.append(df_krx.loc[code, 'Name'])
            corr.append(corr_)

        corr = pd.DataFrame(corr, columns=['code', 'd', 'w', 'm', 'name'])
        corr['average'] = corr[['d', 'w', 'm']].mean(axis=1)
        corr['std']= corr[['d', 'w', 'm']].std(axis=1)
        corr.dropna(inplace=True)
        corr.to_feather('data/corr_fh.feather')

        # example usage
        # corr_top = corr.loc[(corr['average'] > 0.7) & (corr['std'] < 0.1)]
        # corr_inv = corr[corr[['w', 'm']].min(axis=1) > 0.7].sort_values('d')

    def plot_fholdings(self, code):
        drawer = Drawer()
        
        fh, cr = self.fetch_foreign_holdings(code, 'D')
        fh.plot(figsize=(15, 10), secondary_y='fh', title='D')
        fh, cr = self.fetch_foreign_holdings(code, 'W')
        fh.plot(figsize=(15, 10), secondary_y='fh', title='W')
        fh, cr = self.fetch_foreign_holdings(code, 'M')
        fh.plot(figsize=(15, 10), secondary_y='fh', title='M')
        return None