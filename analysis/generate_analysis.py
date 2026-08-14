from trader.analysis.sector_analysis import SectorAnalysis
from scraper.models.component import ComponentManager
from scraper.models.valuechain import ValueChainManager

valuechain_name = "Electronics"
vcm = ValueChainManager()
cm = ComponentManager()
vc = vcm.get_item(key=valuechain_name)

###_ need to add VC financials (save)
# SectorAnalysis().from_codelist(vc.get_codelist_set())

for component_name in vc.components: 
    cp = cm.get_item(component_name)
    # generate sa for component itself
    SectorAnalysis().from_component(cp)

    # generate sa for companies in the component
    for code in cp.get_codelist():
        SectorAnalysis().from_code(code)
