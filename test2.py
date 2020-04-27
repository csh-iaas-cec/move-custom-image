from tqdm import tqdm
import time
name = "kishore"
add_space = " "
print(add_space * 10)
name1 = "kishore kumar raju"
name = name + (add_space * (len(name1)-len(name)))
for i in tqdm(range(100), bar_format='{desc}: {percentage:3.0f}%|{bar} | {n_fmt}/{total_fmt}', desc="Kishore", ncols=100):
    time.sleep(0.1)

for i in tqdm(range(100), bar_format='{desc}: {percentage:3.0f}%|{bar} | {n_fmt}/{total_fmt}', desc="Kishore kumar raju", ncols=100):
    time.sleep(0.1)