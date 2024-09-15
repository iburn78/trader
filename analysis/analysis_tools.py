#%%
import sys, os
sys.path.append(os.path.dirname(os.getcwd()))  
import FinanceDataReader as fdr
from tools.tools import set_KoreaFonts
import matplotlib.pyplot as plt
import pandas as pd

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
    set_KoreaFonts()
    arrowprops = dict(arrowstyle = arrowstyle, lw=line_width, facecolor= line_color, edgecolor= line_color, shrinkA=1, shrinkB=0)
    mid_point = ((sp[0] + ep[0]) / 2, (sp[1] + ep[1]) / 2)
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


import matplotlib.dates as mdates
# price should be the result from the function get_last_N_quarter_price
def quarterly_average_plot(ax, pr, fontsize = 12, precision=0):
    quarters = pd.to_datetime(pr.index).to_period('Q')
    for quarter in quarters.unique():
        start = pd.to_datetime(str(quarter.start_time))
        end = pd.to_datetime(str(quarter.end_time))
        if precision == 0:
            avg_value = int(pr.loc[quarter.start_time:quarter.end_time].mean().round())  # Get the average for the quarter
        else: 
            avg_value = pr.loc[quarter.start_time:quarter.end_time].mean().round(precision)  
        ax.hlines(avg_value, xmin=start, xmax=end, color='orange', linewidth=2, label='quarterly average' if quarter == quarters.unique()[0] else "")
        # Display the average value above the line
        mid_point = start + (end - start) / 2  # Midpoint of the quarter
        ax.text(mid_point, avg_value + (avg_value * 0.01), f'{avg_value}', color='orange', ha='center', va='bottom', fontsize=fontsize)

    ax.text(pr.index[-1], pr.values[-1], f' {pr.values[-1].round(precision)}', ha='left', va='bottom', fontsize = fontsize, color='red')
    # Iterate over each quarter and highlight even-numbered quarters
    for i, quarter in enumerate(quarters.unique()):
        if quarter.quarter % 2 == 0:  # Check if it is an even-numbered quarter
            start = pd.to_datetime(str(quarter.start_time))
            end = pd.to_datetime(str(quarter.end_time))
            ax.axvspan(start, end, facecolor='gray', alpha=0.2)  # Fill with a white box

    # Generate tick positions at the center of each quarter
    tick_positions = [(pd.to_datetime(str(q.start_time)) + (pd.to_datetime(str(q.end_time)) - pd.to_datetime(str(q.start_time))) / 2) for q in quarters.unique()]

    # Custom function to format x-axis ticks as yy.q
    def format_quarter(x, pos=None):
        date = mdates.num2date(x)
        year_short = date.year % 100  # Get last two digits of the year (e.g., 2024 -> 24)
        quarter = (date.month - 1) // 3 + 1
        return f'{year_short}.{quarter}'

    # Set tick positions and custom tick formatter
    ax.set_xticks(tick_positions)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(format_quarter))
    

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


def save_line_plot(data, type, output_file):
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
        
    spine_color = 'lightgray'
    background_color = '#001f3f'  # deep dark blue
    figsize = (16, 9)
    ax_size = [0.05, 0.05, 0.9, 0.9]
    text_size = 18
    tick_text_size = 15

    set_KoreaFonts()
    plt.rcParams.update({
        'axes.edgecolor': spine_color,
        'axes.labelcolor': spine_color,
        'xtick.color': spine_color,
        'ytick.color': spine_color,
        'xtick.labelsize': tick_text_size,
        'ytick.labelsize': tick_text_size,
        'text.color': spine_color,
    })
    fig = plt.figure(figsize=figsize)
    ax = fig.add_axes(ax_size)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    fig.patch.set_facecolor(background_color)  # Figure background color
    ax.set_facecolor(background_color)
    ax.text(0, 1.01, f'({unit_text})', fontsize=tick_text_size, color=spine_color, ha='left', va='bottom', transform=ax.transAxes)
    ax.text(1, 1.01, f'({data.index[-1].date()})', fontsize=tick_text_size, color=spine_color, ha='right', va='bottom', transform=ax.transAxes)
    ax.set_title(type, fontsize=text_size)
    ax.set_xlabel('quarters', fontsize=tick_text_size)

    ax.plot(data)
    quarterly_average_plot(ax, data, tick_text_size, precision=precision)

    fig.savefig(output_file, format='png', transparent=True, bbox_inches='tight', pad_inches=0.2)


