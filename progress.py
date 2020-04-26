import concurrent.futures

from tqdm import tqdm


import time
time.sleep(5)
def prog(per, name):
    with tqdm(total=100, desc = name) as progress_bar:
        temp=0
        for i in per:
            progress_bar.update(i-temp)
            temp=i

def show_progress(percent, names):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        res = [executor.map(prog, percent, names)]

