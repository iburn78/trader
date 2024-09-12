#%%
import sys, os
sys.path.append(os.path.dirname(os.getcwd()))  
import FinanceDataReader as fdr
from analysis_tools import *
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import matplotlib.dates as mdates
import pandas as pd

code = '005930'
START_DATE = '2014-01-01'
start_qts_back = 6  # Define how many quarters back you want to start from
output_file = f'plots/plot_price.png'

spine_color = 'lightgray'
background_color = '#001f3f'  # deep dark blue
figsize = (16, 8)
ax_size = [0.05, 0.05, 0.9, 0.9]
text_size = 25
tick_text_size = 20

font_path = r'C:\Windows\Fonts\NanumGothic.ttf'
font_prop = FontProperties(fname=font_path)
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
ax_size_in_px = (int(72*figsize[0]*ax_size[2]), int(72*figsize[1]*ax_size[3]))
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.patch.set_facecolor(background_color)  # Figure background color
ax.set_facecolor(background_color)

ax.set_title('주가', fontproperties=font_prop, fontsize=text_size)
ax.set_xlabel('quarters', fontsize=tick_text_size)

pr_raw = fdr.DataReader(code, START_DATE)['Close']

last_date = pr_raw.index[-1]
# Calculate the month of the current quarter
quarter_month = ((last_date.month - 1) // 3) * 3 + 1
# Calculate the first day of the quarter start_qts_back quarters before last_date
start_date = pd.Timestamp(year=last_date.year, month=quarter_month, day=1) - pd.DateOffset(months=3 * start_qts_back)

pr = pr_raw.loc[start_date:]
ax.plot(pr, label="price")

# Set y-axis label and add unit text
# ax.set_ylabel('Price', fontsize=tick_text_size)
ax.text(0, 1.02, '(원)', fontproperties=font_prop, fontsize=tick_text_size, color=spine_color, ha='left', va='bottom', transform=ax.transAxes)

quarters = pd.to_datetime(pr.index).to_period('Q')
pr_av = pr.groupby(quarters).transform('mean')

# Plot the quarterly averages as horizontal lines
for quarter in quarters.unique():
    start = pd.to_datetime(str(quarter.start_time))
    end = pd.to_datetime(str(quarter.end_time))
    avg_value = int(pr.loc[quarter.start_time:quarter.end_time].mean().round())  # Get the average for the quarter
    ax.hlines(avg_value, xmin=start, xmax=end, color='orange', linewidth=2, label='quarterly average' if quarter == quarters.unique()[0] else "")
    # Display the average value above the line
    mid_point = start + (end - start) / 2  # Midpoint of the quarter
    ax.text(mid_point, avg_value + (avg_value * 0.01), f'{avg_value}', color='orange', ha='center', va='bottom', fontsize=tick_text_size)

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

fig.savefig(output_file, format='png', transparent=True, bbox_inches='tight', pad_inches=0.2)
plt.show()
