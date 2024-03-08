    # to collect a single company data and plot it:
    # code = '001890'
    # db = single_company_data_collect(code)
    # or 
    # main_db = pd.read_feather(main_db_file)
    # db = main_db.loc[main_db['code'] == code]
    # pd.set_option('display.max_columns', None)
    # db=db.dropna(axis=1, how='all')
    # display(db)
    # path = 'plots/'+code+'.png'
    # plot_company_financial_summary(db, code, path)
    # dart = OpenDartReader(DART_APIS[0])
    # a = dl.corp_codes(DART_APIS[0])
    # display(a)
    # print(a.loc[a['corp_name'].str.contains('', case=False)])
