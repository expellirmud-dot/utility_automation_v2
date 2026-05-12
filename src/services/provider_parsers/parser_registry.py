from src.services.provider_parsers.nt_parser import NTParser
from src.services.provider_parsers.electricity_parser import ElectricityParser
from src.services.provider_parsers.water_parser import WaterParser

class ParserRegistry:
    _parsers = [NTParser(), ElectricityParser(), WaterParser()]

    @classmethod
    def get_parser(cls, bill_data):
        for parser in cls._parsers:
            if parser.can_handle(bill_data):
                return parser
        return None
