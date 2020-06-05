from config import Config
import oci
import logs
import argparse

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
                    if(image_detail.lifecycle_state == "DELETED" or image_detail.lifecycle_state == "UNKNOWN_ENUM_VALUE"):
                        print(f"Import of image {image_detail.display_name} is deleted or unknown in {region}")
                    elif(image_detail.lifecycle_state == "AVAILABLE"):
                        print(f"Successful import of image {image_detail.display_name}, import COMPLETED in {region}")
                    elif(image_detail.lifecycle_state == "IMPORTING"):
                        print(f"Please wait and try again, importing of image {image_detail.display_name} in {region}")
                except Exception as e:
                    logger.error(e)
                    print(f"Image does't exist or we dont have a trace of existence. Please retry copying of image {image_detail.display_name} in {region}")
    except Exception:
        logger.error(f"image_details.txt doesnt exist")
        print("image_details.txt doesnt exist")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--profile', help='Provide the profile to be used', required=True)
    args = parser.parse_args()
    PROFILE = args.profile
    validate(PROFILE)