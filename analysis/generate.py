from trader.analysis.sector_analysis import SectorAnalysis
from scraper.models.valuechain import ValueChainManager

vc_name = "Electronics"
vm = ValueChainManager()
vc = vm.get_item(vc_name)

#1) need to add VC financials (save)
SectorAnalysis().from_valuechain(vm, vc)

for cp in vm.get_components(vc):
    # 2) generate sa for component itself
    SectorAnalysis().from_component(cp)

    # 3) generate sa for companies in the component
    for code in cp.get_codelist():
        SectorAnalysis().from_code(code)
