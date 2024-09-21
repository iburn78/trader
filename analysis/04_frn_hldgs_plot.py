#%% 
from analysis_tools import *

broker = Broker()
fhd = Drawer()
code = '005930'
period = 'M'
output_file = f'plots/plot_corr_{code}{period}.png'
fh, cr = broker.fetch_foreign_holdings(code, period)
fhd.plot_fholdings(fh, cr, period, output_file)

num_to_plot = 100
figsize = (12,10)
period = 'D' 
output_file = 'plots/plot_corr_compaprison.png'
fhd.corr_comparison_plot(broker, code, period, figsize, num_to_plot, output_file)


# def corr_comparison_plot(broker, code, period = 'M', figsize = (10,10), num_to_plot = 500, output_file=None):
#     threshold = 45
#     crd = Drawer(figsize=figsize)
#     crd._init_fig()

#     corr_data_file = 'data/corr_fh.feather'
#     corr = read_or_regen(corr_data_file, broker.generate_corr_data)

#     sorted_corr = corr.sort_values(period, ascending=True)[-num_to_plot:].reset_index(drop=True)
#     bars = crd.ax.barh(sorted_corr['name'], sorted_corr[period])
#     crd.ax.set_ylim(-0.5, len(bars)-0.5)
#     crd.ax.text(1, 1.01, f'{corr.loc[0, "date"].strftime("%Y-%m-%d")}', fontsize=crd.tick_text_size, color=crd.label_text_color, ha='right', va='bottom', transform=crd.ax.transAxes)
#     crd.ax.set_title(f'외국인 보유율과 주가 상관관계', fontsize=crd.text_size)
#     crd.ax.text(0.5, 0.05, f'(시총>{format(int(Broker.MARCAP_THRESHOLD/10**8),",")}억원, 상장>{int(Broker.IPO_YEAR_THRESHOLD)}년인 상장사 총{len(corr)}개 중 상위{min(len(corr), num_to_plot)}개 표시)', ha='center', va='center', transform=crd.ax.transAxes,  # Use axes coordinates
#             bbox=dict(facecolor='black', edgecolor='none', boxstyle='round,pad=0.3'),
#             fontsize=crd.tick_text_size, color='white', zorder=5)  # Ensure text is on top

#     target_row = sorted_corr.loc[sorted_corr['code'] == code]
#     if len(target_row)>0:
#         code_loc = target_row.index[0]
#         bars[code_loc].set_color('orange')

#         target_name = target_row['name'].values[0]
#         target_ranking = len(sorted_corr) - code_loc
#         crd.ax.text(0.5, 0.10, f'{target_name}: {target_ranking}번째로 상관관계 높음', ha='center', va='center', transform=crd.ax.transAxes,  # Use axes coordinates
#                 bbox=dict(facecolor='green', edgecolor='none', boxstyle='round,pad=0.3'),
#                 fontsize=crd.text_size, color='white', zorder=5)  # Ensure text is on top

#     if num_to_plot > threshold: 
#         crd.ax.set_yticks([]) 
#     else: 
#         for bar in bars:
#             xval = round(bar.get_width(), 2)
#             yval = bar.get_y() + bar.get_height()/2
#             crd.ax.text(xval*1.01, yval, f'{xval}', va='center', ha='left', fontsize = crd.tick_text_size )

#     if output_file != None:
#         crd.fig.savefig(output_file, format='png', transparent=True, bbox_inches='tight', pad_inches=0.2)

#     plt.show()
#     plt.close(crd.fig)
