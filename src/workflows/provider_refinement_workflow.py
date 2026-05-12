from src.services.provider_parsers.parser_registry import ParserRegistry

class ProviderRefinementWorkflow:
    @staticmethod
    def run(bill_data):
        parser = ParserRegistry.get_parser(bill_data)
        if parser:
            try:
                return parser.refine(bill_data)
            except Exception as e:
                bill_data.extraction_notes.append(f"Refinement error: {str(e)}")
        
        return bill_data
