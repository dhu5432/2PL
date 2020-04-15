import random
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--file', help= 'Include which text file to run')
args = parser.parse_args()

file1 = open(args.file, "w")
for i in range(0, 7000):
    str1 = "BT\nR {} BALANCE\nW {} ASSETS 3\nC\n".format(random.randint(1, 899), random.randint(1,899))
    file1.write(str1)

