
# /home/pcl/8LStudentYuHaitao/passive-2016/equinix-chicago/20160121-130000.UTC/equinix-chicago.dirA.20160121-125911.UTC.anon.pcap.gz
# tshark -r "$pcap" | awk '{print $2 "," $3 "," $5 "," $6 "," $7 "," $8 "," $10}'

#################################
import pandas as pd
import os
# d = pd.read_csv("../tmp/test2all.dat",error_bad_lines =False,names=['time','src','dst','proto', 'vol','src_port','dst_port'])

DATADIR="../tmp/data"

ii=0
for root, dirs, files in os.walk(DATADIR):
    print(root)
    print(dirs)
    print(files)
    for f in files:
        d = pd.read_csv(DATADIR+"/"+f, error_bad_lines =False,names=['time','src','dst','proto', 'vol','src_port','dst_port'])
        dns=d[(d['dst_port']=='53')]
        dns.to_csv("i"+str(ii)+".csv",index=False)
        ii+=1



#################################
import pandas as pd
import os
DATADIR="../tmp/data"
import  multiprocessing as mp
p = mp.Pool(processes=32)

def worker(f,ii):
    d = pd.read_csv(DATADIR+"/"+f, error_bad_lines =False,names=['time','src','dst','proto', 'vol','src_port','dst_port'])
    dns=d[(d['dst_port']=='123') & (d['proto']=='UDP')]
    dns.to_csv("ntp"+str(ii)+".csv",index=False)

ii=0
for root, dirs, files in os.walk(DATADIR):
    print(root)
    print(dirs)
    print(files)
    for f in files:
        p.apply(worker,(f,ii))
        ii+=1

p.close()
p.join()









#################################
alldf=[]
for i in range(ii):
    df = pd.read_csv("i"+str(i)+".csv");
    alldf.append(df)
df = pd.concat(alldf,axis=0,ignore_index=True)



import pyasn

DEFAULT_ASNDB='../sfp-eval/ipasn.20190116.1600.dat'
asndb = pyasn.pyasn(DEFAULT_ASNDB)
# src_asn = asndb.lookup(columns[1])[0]

stat={}
for i,dd in df.iterrows():
    srcas = asndb.lookup(str(dd.src))[0]
    if not srcas:
        continue
    stat.setdefault(srcas,{})
    dnsserver = str(dd.dst)
    stat[srcas][dnsserver] = stat[srcas].get(dnsserver,0)+int(dd.vol)



#######################



from matplotlib import pyplot as plt


def plot1(stat):
    xlabel=[]
    y=[]
    for k,v in stat.items():
        xlabel.append(str(k))
        yy=list(v.values())
        y.append(yy)

    ml = max(len(yi) for yi in y)

    for yi in y:
        if len(yi)<ml:
            yi.extend([0 for _ in range(ml-len(yi))])
        yi.sort(reverse = True)

    x=list(range(len(xlabel)))

    ry=[]
    for yy in y:
        yyy=yy[:10]
        ry.append(list(sum(yyy[i:]) for i in range(len(yyy))))


    for i in range(min(ml,10)):
        py = [ry[ii][i] for ii in x]
        plt.bar(x, py)
    plt.show()

plot1(stat)


def plot2(stat):
    xlabel=[]
    y=[]
    for k,v in stat.items():
        xlabel.append(str(k))
        yy=list(v.values())
        y.append(yy)

    ml = max(len(yi) for yi in y)

    for yi in y:
        if len(yi)<ml:
            yi.extend([0 for _ in range(ml-len(yi))])
        yi.sort(reverse = True)

    x=list(range(len(xlabel)))

    ry=[]
    for yy in y:
        ry.append(list(sum(yy[i:])/float(sum(yy)) for i in range(10)))


    for i in range(min(ml,10)):
        py = [ry[ii][i] for ii in x]
        plt.bar(x, py)
    plt.show()

plot2(stat)

