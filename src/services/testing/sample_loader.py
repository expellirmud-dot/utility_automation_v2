import os

class SampleLoader:
    @staticmethod
    def get_all_samples(base_path="samples/Input_Bills"):
        samples = []
        for root, dirs, files in os.walk(base_path):
            for file in files:
                if file.endswith(".pdf"):
                    samples.append(os.path.join(root, file))
        return samples
