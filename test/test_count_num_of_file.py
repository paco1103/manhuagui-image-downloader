import os

base_path = '/app/不正经的魔术讲师与禁忌教典'

for directory in os.listdir(base_path):
    if 'pdf' in directory:
        continue
    print(directory, len(os.listdir(base_path + '/'+ directory)))
