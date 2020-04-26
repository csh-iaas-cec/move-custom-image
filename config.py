from oci.config import from_file

class Config:
    def __init__(self, profile):
        self.config = from_file('~/.oci/config',profile)

    def set_region(self, region):
    	self.config["region"] = region

    def get_config(self):
    	return self.config


    