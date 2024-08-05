from sys import argv
from comlier import complier

"""
-c ${ProjectPath} [${OutputPath}] [${CompilerOptions}]

"""

def help():
    print("cpm version: -v1.0")
    print("commend:")
    print("\t-c: auto complier project")

if len(argv) <= 1:
    help()

commends = []
sign = False
for word in argv:
    if not sign:
        sign = True
        continue

    if word[0] == "-":
        commends.append([word])
    else:
        commends[-1].append(word)

for option in commends:
    if option[0] == '-c':
        complier(option[1:])