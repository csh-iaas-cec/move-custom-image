from config import Config
import oci
import logs

logger = logs.logger

def get_destination_compute_client(profile, region):
    config = Config(profile)
    config.set_region(region)
    config = config.get_config()
    return oci.core.ComputeClient(config)

def validate(profile):
    try:
        with open("images_details.txt", 'r') as f:
            ocids = f.readlines()
            for image_details in ocids:
                try:
                    detail = image_details.strip().split(",")
                    image_id = detail[0]
                    region = detail[1]
                    cid = get_destination_compute_client(profile, region)
                    image_detail = cid.get_image(image_id).data
                    if(image_detail.lifecycle_state == "DELETED" || image_detail.lifecycle_state == "UNKNOWN_ENUM_VALUE"):
                        print(f"Import of image {image_detail.display_name} is deleted or unknown")
                except Exception as e:
                    logger.error(e)
                    print(f"Image does't exist or we dont have a trace of existence. Please retry copying of image {image_detail.display_name}")
    except Exception:
        logger.error(f"image_details.txt doesnt exist")
        print("image_details.txt doesnt exist")

if __name__ == "__main__":
    description = "\n".join(["Migrates the custom images to given destination regions","pip install -r requirements.txt","python migrate.py <images_list_file_name.txt> iad lhr bom phx"])
	parser = argparse.ArgumentParser(description=description,
									 formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.add_argument('--profile', help='Provide the profile to be used', required=True)
    args = parser.parse_args()
	PROFILE = args.profile
	if(args.bucket_name):
		bucket_name = args.bucket_name
    validate(PROFILE)