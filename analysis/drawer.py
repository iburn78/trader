#%% 
import sys, os
sys.path.append(os.path.dirname(os.getcwd()))  
from tools.tools import set_KoreanFonts
from tools.koreainvest_module import *
from analysis_tools import *
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
import pandas as pd
from broker import Broker

class Drawer:

    def __init__(
            self, 
            spine_color = 'lightgray',
            background_color = '#001f3f',  # deep dark blue
            figsize = (16, 9),
            ax_size = [0.05, 0.05, 0.9, 0.9],
            text_size = 18,
            tick_text_size = 15,
            label_text_color = 'gray',
            lang = 'K',
            eng_name = None
        ):
        self.spine_color = spine_color
        self.background_color = background_color
        self.figsize = figsize
        self.ax_size = ax_size
        self.text_size = text_size
        self.tick_text_size = tick_text_size
        self.label_text_color = label_text_color
        self.lang = lang
        self.eng_name = eng_name

        set_KoreanFonts()
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
    
    def _init_twinx(self):
        self.tax = self.ax.twinx()
        self.tax.spines['top'].set_visible(False)
        self.tax.set_facecolor(self.background_color)
        
    def draw_arrow(self, sp, ep, 
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
        self.ax.annotate('', xy=ep, xytext=sp, arrowprops=arrowprops)
        self.ax.annotate(text, xy=mid_point, xytext=text_offset, textcoords='offset points', ha='center', va='bottom', fontsize=text_size, color=text_color)
        # ax.annotate(text, xy=mid_point, xytext=text_offset, textcoords='offset points', ha='center', va='bottom', fontproperties= font_prop, fontsize=text_size, color=text_color)
        return None

    def draw_text(self, pt, text, **kwargs):
        self.draw_arrow(pt, pt, text=text, arrowstyle='->', **kwargs)

    def draw_line(self, sp, ep, **kwargs):
        self.draw_arrow(sp = sp, ep = ep, arrowstyle='-', **kwargs)

    def draw_increase(self, sp, ep, ext = 1, pos = 0.85, **kwargs):
        (spx, spy) = sp
        (epx, epy) = ep
        self.draw_line(sp, (epx+ext, spy), line_color='whitesmoke', line_width = 1, **kwargs)
        self.draw_line(ep, (epx+ext, epy), line_color='whitesmoke', line_width = 1, **kwargs)
        if spy*epy > 0:
            increment = str(round((epy/spy-1)*100)) + '%'
        self.draw_arrow((epx+ext*pos, spy), (epx+ext*pos, epy), text=increment, line_width=2, **kwargs )
    
    def pt_iqbefore(self, ith, quarters_list, y_values): # ith = 0, this quarter (last bar)
        # quarters_list: return value of get_quarters()
        x_idx = len(quarters_list)-ith-1
        return (x_idx, y_values[x_idx])

    def _format_quarter(x, pos=None): 
        date = mdates.num2date(x)
        year_short = date.year % 100  
        quarter = (date.month - 1) // 3 + 1
        return quarter_format(year_short, quarter)

    def _get_unit_base(self, unit_base):
        unit_dict = {1: lang_formatter('KRW', self.lang), 3: lang_formatter('K KRW', self.lang), 6: lang_formatter('M KRW', self.lang), 8: lang_formatter('100M KRW', self.lang), 9: lang_formatter('B KRW', self.lang), 12: lang_formatter('T KRW', self.lang)}
        return unit_dict.get(unit_base, 'UNIT_ERROR')
    
    def _savefig(self, output_file): 
        output_file = output_file[:-4]+'_'+self.lang+output_file[-4:]
        self.fig.savefig(output_file, format='png', transparent=True, bbox_inches='tight', pad_inches=0.2)

    def save_bar_plot(self, fh, target_account, num_qts, unit, unit_base, increment_FT, lim_scale_factor, output_file, bar_highlights = None, bar_highlights_gray = None):
        self._init_fig()
        x = get_quarters(get_last_quarter(fh), num_qts)
        xs = get_quarter_simpler_string(x)
        y = (fh.loc[fh['account'] == target_account, x]/((10**unit_base)*unit)).round(1).values.flatten()
        bars = self.ax.bar(xs,y)

        light_orange = (1.0, 0.8, 0.6)  # Lighter shade of orange
        if bar_highlights == None: 
            bars[-1].set_color('orange')
            for i in range(1, len(bars)+1, 4):
                bars[-i].set_color('orange')
        else: 
            for i in bar_highlights:
                bars[-i].set_color('orange')

        if bar_highlights_gray != None: 
            for j in bar_highlights_gray:
                bars[-j].set_color('gray')

        for bar in bars:
            yval = bar.get_height()
            if yval < 100:
                yval = round(yval, 1)
            else:
                yval = int(yval)
            self.ax.text(bar.get_x() + bar.get_width()/2, yval, f'{format(yval, ",")}', ha='center', va='bottom', fontsize = self.tick_text_size )

        self.ax.set_xlim(-1, len(x))
        ymax = max(int(max(y)*1.1), int(max(y)*lim_scale_factor))
        ymin = min(int(min(y)*1.1), int(min(y)*lim_scale_factor))
        self.ax.set_ylim(ymin, ymax)  
        self.ax.set_title(lang_formatter(target_account.replace('_', ' '), self.lang), fontsize = self.text_size)
        # self.ax.set_xlabel(lang_formatter('quarters', self.lang), fontsize = self.tick_text_size, color= self.label_text_color)

        # self.draw_text((-0.5, ymax), f'(x {format(unit, ",")} {self._get_unit_base(unit_base)})', text_size = self.tick_text_size, text_color=self.label_text_color)
        self.ax.set_ylabel(f'(x {format(unit, ",")}{" " if unit_base == 8 else ""}{self._get_unit_base(unit_base)})', fontsize = self.tick_text_size, color=self.label_text_color) 
        self.ax.yaxis.set_major_formatter(ticker.FuncFormatter(precision_formatter))

        if increment_FT[0] != increment_FT[1]:
            sp = self.pt_iqbefore(increment_FT[0] , x, y)
            ep = self.pt_iqbefore(increment_FT[1], x, y)
            ax_size_in_px = (int(72*self.figsize[0]*self.ax_size[2]), int(72*self.figsize[1]*self.ax_size[3]))
            bar_distance_px = int(ax_size_in_px[0]/(2+len(x)))
            self.draw_increase(sp, ep, text_offset = (int(bar_distance_px/2)+2, -self.text_size/2), text_size = self.text_size)

        if output_file != None:
            self._savefig(output_file)
        plt.show()
        plt.close(self.fig)

    def save_line_plot(self, data, type, subgraph, output_file):  
        self._init_fig()

        # type : price, PER, PBR
        # subgraph : quarterly, average
        if type == 'price':
            unit_text = lang_formatter('KRW', self.lang)
            precision = 0
        elif type == 'PER':
            unit_text = lang_formatter('multiple', self.lang)
            precision = 2
        elif type == 'PBR': 
            unit_text = lang_formatter('multiple', self.lang)
            precision = 3
        else: 
            pass

        self.ax.text(0, 1.01, f'({unit_text})', fontsize=self.tick_text_size, color=self.label_text_color, ha='right', va='bottom', transform=self.ax.transAxes)
        self.ax.text(1, 1.01, f'({data.index[-1].date()})', fontsize=self.tick_text_size, color=self.label_text_color, ha='right', va='bottom', transform=self.ax.transAxes)
        self.ax.set_title(lang_formatter(type, self.lang), fontsize=self.text_size, weight='bold')
        # self.ax.set_xlabel(lang_formatter('quarters', self.lang), fontsize=self.tick_text_size)
        self.ax.yaxis.set_major_formatter(ticker.FuncFormatter(precision_formatter))

        self.ax.plot(data)
        if subgraph == 'quarterly':
            self._quarterly_average_plot(data, precision=precision)
        elif subgraph == 'average':
            self._average_plot(data, precision=precision)
        else:
            pass
        if output_file != None:
            self._savefig(output_file)
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

    def _price_xtick_formatter(self, pr):
        quarters = pd.to_datetime(pr.index).to_period('Q')
        # Generate tick positions at the center of each quarter
        tick_positions = [(pd.to_datetime(str(q.start_time)) + (pd.to_datetime(str(q.end_time)) - pd.to_datetime(str(q.start_time))) / 2) for q in quarters.unique()]

        # Set tick positions and custom tick formatter
        self.ax.set_xticks(tick_positions)
        self.ax.xaxis.set_major_formatter(plt.FuncFormatter(Drawer._format_quarter))

        if self._check_xtick_label_overlap(): 
            self.ax.xaxis.set_major_locator(mdates.YearLocator())  # Set major ticks to years
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))  # Format ticks to show only the year

            # self.ax.xaxis.set_major_locator(mdates.AutoDateLocator())  # Automatically set date ticks
            # self.ax.xaxis.set_major_formatter(mdates.AutoDateFormatter(self.ax.xaxis.get_major_locator()))  # Set date formatter

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
        self.draw_arrow((pr.index[arrow_point], avg_value*(1.0)), (pr.index[arrow_point], upper_value), '+1$\sigma$', text_offset=(17, 0))
        self.draw_arrow((pr.index[arrow_point], avg_value*(1.0)), (pr.index[arrow_point], lower_value), '-1$\sigma$', text_offset=(17, 0))
        self._price_xtick_formatter(pr)

    def plot_fownership(self, fh, cr, period='D', output_file=None):
        # period = 'D', 'W', 'M'
        self._init_fig()
        self._init_twinx()

        self.ax.grid(True, color='gray', linestyle='--', linewidth=0.5)
        x_locs = range(len(fh))
        self.ax.plot(x_locs, fh['price'], '-o', linewidth = 1, label = 'price')
        self.ax.set_xticks(x_locs)  # Set the tick locations
        self.ax.set_xticklabels(fh.index.strftime('%m-%d'), rotation=45)  # Set the tick labels with rotation
        self.tax.plot(x_locs, fh['fh'], ':o', color='r', linewidth = 2, label=lang_formatter('foreigner', self.lang))

        # self.ax.set_xlabel('Dates', fontsize = self.tick_text_size, color=self.label_text_color)
        self.ax.set_ylabel(f'Price({lang_formatter("KRW", self.lang)})', fontsize = self.tick_text_size, color=self.label_text_color)

        if self.lang == 'K':
            period_dict = {'D': '(최근 30일)', 'W': '(최근 30주)', 'M': '(최근 30개월)'}
            title = '주가, 외국인 보유율 '
            ylabel = '외국인 보유율(%)'
            corr_text = '상관계수'
        else: 
            period_dict = {'D': '(Last 30 days)', 'W': '(Last 30 weeks)', 'M': '(Last 30 months)'}
            title = 'Price and Foreign ownership'
            ylabel = 'Foreign ownership ratio(%)'
            corr_text = 'Correlation coefficient'
        
        self.ax.set_title(title+period_dict[period], fontsize = self.text_size)
        self.tax.set_ylabel(ylabel, fontsize = self.tick_text_size, color=self.label_text_color)
        self.ax.legend(framealpha=0, loc='upper left', fontsize = self.tick_text_size, bbox_to_anchor=(0,1.05))
        self.tax.legend(framealpha=0, loc='upper right', fontsize = self.tick_text_size, bbox_to_anchor=(1,1.05))
        self.ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{int(x):,}'))

        name = lookup_name_onetime(fh['code'].iloc[0], self.lang, self.eng_name)
        self.ax.text(0.5, 0.07, f'{name} {corr_text}: '+str(round(cr, 2)), ha='center', va='center', transform=self.ax.transAxes,  # Use axes coordinates
                bbox=dict(facecolor='green', edgecolor='none', boxstyle='round,pad=0.3'),
                fontsize=self.text_size, color='white', zorder=5)  # Ensure text is on top
        if output_file != None:
            self._savefig(output_file)

        plt.show()
        plt.close(self.fig)

    def corr_comparison_plot(self, broker, code, period = 'M', figsize = (10,10), num_to_plot = 500, text_label = True, output_file=None):
        threshold = 45
        self.figsize = figsize
        self._init_fig()

        corr_data_file = 'data/corr_fownership.feather'
        corr = read_or_regen(corr_data_file, broker.generate_corr_data)

        if self.lang == 'K':
            title = '외국인 보유율과 주가 상관관계'
            text_01 = f'(시총>{format(int(Broker.MARCAP_THRESHOLD/10**8),",")}억원, 상장>{int(Broker.IPO_YEAR_THRESHOLD)}년인 상장사 총{len(corr)}개 중 상관계수 상위{min(len(corr), num_to_plot)}개 표시)'
        else: 
            title = 'Share price and Foreign ownership correlation '
            text_01 = f'(total {len(corr)} public companies are Market Cap > {format(int(Broker.MARCAP_THRESHOLD/10**9),",")}B KRW, IPO > {int(Broker.IPO_YEAR_THRESHOLD)} years, and top {min(len(corr), num_to_plot)} are shown)'

        sorted_corr = corr.sort_values(period, ascending=True)[-num_to_plot:].reset_index(drop=True)
        bars = self.ax.barh(sorted_corr['name'], sorted_corr[period])
        self.ax.set_ylim(-0.5, len(bars)-0.5)
        self.ax.text(1, 1.01, f'{corr.loc[0, "date"].strftime("%Y-%m-%d")}', fontsize=self.tick_text_size, color=self.label_text_color, ha='right', va='bottom', transform=self.ax.transAxes)
        self.ax.set_title(title, fontsize=self.text_size)
        if text_label: 
            self.ax.text(0.5, 0.05, text_01, ha='center', va='center', transform=self.ax.transAxes,  # Use axes coordinates
                    bbox=dict(facecolor='black', edgecolor='none', boxstyle='round,pad=0.3'),
                    fontsize=self.tick_text_size, color='white', zorder=5)  # Ensure text is on top

        target_row = sorted_corr.loc[sorted_corr['code'] == code]
        if len(target_row)>0:
            code_loc = target_row.index[0]
            bars[code_loc].set_color('orange')

            target_name = lookup_name_onetime(code, self.lang, self.eng_name)
            target_ranking = len(sorted_corr) - code_loc
            if self.lang == 'K':
                text_02 = f'{target_name}: {target_ranking}번째로 상관관계 높음'
            else: 
                text_02 = f'{target_name}: top {target_ranking} in terms of correlation coefficient'

            if text_label:
                self.ax.text(0.5, 0.10, text_02, ha='center', va='center', transform=self.ax.transAxes,  # Use axes coordinates
                        bbox=dict(facecolor='green', edgecolor='none', boxstyle='round,pad=0.3'),
                        fontsize=self.text_size, color='white', zorder=5)  # Ensure text is on top

        if num_to_plot > threshold: 
            self.ax.set_yticks([]) 
        else: 
            for bar in bars:
                xval = round(bar.get_width(), 2)
                yval = bar.get_y() + bar.get_height()/2
                self.ax.text(xval*1.01, yval, f'{xval}', va='center', ha='left', fontsize = self.tick_text_size )

        if output_file != None:
            self._savefig(output_file)

        plt.show()
        plt.close(self.fig)