#!/usr/bin/env python3

if __name__ == '__main__':
    import sys
    with open(sys.argv[1], 'r') as f:
        lines = f.readlines()
        for i in range(0, len(lines), 3):
            asn = lines[i].strip('\n').strip(' ')[2:]
            country = lines[i+1].strip('\n')[-2:]
            print(asn + '|' + country)
