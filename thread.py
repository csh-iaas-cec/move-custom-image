import sys
import time
import concurrent.futures

from percent_complete import PercentComplete


def printProgressBar(
    iteration,
    total,
    prefix="",
    suffix="",
    decimals=1,
    length=100,
    fill="█",
    printEnd="\r",
):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + "-" * (length - filledLength)
    print("\r%s |%s| %s%% %s" % (prefix, bar, percent, suffix), end="\r\n\r")

    # sys.stdout.write("\r%s |%s| %s%% %s" % (prefix, bar, percent, suffix))
    # sys.stdout.flush()
    if iteration == total:
        print()


image_id2 = "ocid1.image.oc1.phx.aaaaaaaayhsmp6jfh44asatnz2dhrys7hrubdryblpqnw7vr3fhvft5m6nmq"
image_id = "ocid1.image.oc1.phx.aaaaaaaac7w2dmqra4lhhacqiq7c4ayzmlgopy6doekgasytdmhvoml3h62q"
per1 = PercentComplete("informatica-phoenix", image_id)
per2 = PercentComplete("informatica-phoenix", image_id2)
# image_details = per1.worker.get_images_details(image_id)
# per2.worker.export_image(image_details)
# image_details = per2.worker.get_images_details(image_id2)
# per2.worker.export_image(image_details)
time.sleep(5)
def progress(per, name):
    printProgressBar(0, 100, prefix=name+":", suffix="Complete", length=50)
    print()
    for i in per:
        printProgressBar(i, 100, prefix=name+":", suffix="Complete", length=50)

with concurrent.futures.ThreadPoolExecutor() as executor:
    t = [per1, per2]
    name = ["kishore", "kumar"]
    res = [executor.map(progress, t, name)]

