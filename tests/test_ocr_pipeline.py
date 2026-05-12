import os
from src.workflows.process_pdf_workflow import ProcessPDFWorkflow

def test_pipeline():
    # Path to sample PDF (assuming user places a sample in samples/ directory)
    sample_path = os.path.join("samples", "test.pdf")
    
    if not os.path.exists(sample_path):
        print(f"Sample file not found at {sample_path}. Please place a test PDF there.")
        return

    print("Processing PDF...")
    result = ProcessPDFWorkflow.run(sample_path)
    
    print("\nOCR Result:")
    print(result)
    
    # Save output
    output_path = os.path.join("output", "extracted_text.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result.extracted_text)
    
    print(f"\nExtracted text saved to {output_path}")

if __name__ == "__main__":
    test_pipeline()
