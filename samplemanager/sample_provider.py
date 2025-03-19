class SampleProvider:
    def __init__(self, nanoAOD_version: int = 9):
        self.nanoAOD_version = nanoAOD_version

    # returns the datasets.json for a given nanoAOD version
    def get_datasets(self):
        return

    # returns the sample data for a given nanoAOD version, era, sample_type and nick
    def get_sample(self, nick: str):
        return