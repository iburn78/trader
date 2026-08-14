from trader.analysis.sector_analysis import SectorAnalysis
from scraper.models.component_manager import ComponentManager

component_name = "Memory"
component = ComponentManager().get_item(component_name)

# generate sa for component itself
SectorAnalysis().from_component(component)

# generate sa for companies in the component
for code in component.get_codelist():
    SectorAnalysis().from_code(code)


