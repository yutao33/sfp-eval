
this is partially forked from SFP repository

# Analysis of Internet Topology

All the analysis are based on the public Internet dataset.

## Load Network Topology with AS Relationships

First retrieve the as relationships dataset from CAIDA:

``` sh
$ ./retrive_as_rel.sh
```

Then parse the as relationships to generate the network graph

``` python
from as_rel import load_as_rel
dg = load_as_rel('20181201.as-rel.txt')
```

## Load Internet AS Types

Retrieve the as classification dataset from CAIDA:

``` sh
$ ./retrive_as_types.sh
```

Then parse the as classification to label the type for each network:

``` python
from as_rel import load_as_type
load_as_type('20150801.as2types.txt', dg)
```

Read all stub network:

``` python
from as_rel import get_stub_networks
stubs = get_stub_networks(dg)
print(stubs)
```

## Get Stub Networks Groups

``` sh
$ ./split_as_stubs.py 20181201.as-rel.txt 20150801.as2types.txt > stubs.txt
```

## Retrieve the AS Country Information

``` sh
$ ./retrieve_as_country.sh
```

This script will write down a `as-country.txt` file in the current working directory.

## Load Country-Specific Topology

Label the country information to the existing Internet graph:

``` python
from as_rel import load_as_country
load_as_country('as-country.txt', dg)
```

Get the subgraph for some specific country:

``` python
from as_rel import get_subtopo
sdg = get_subtopo(dg, country='US')
```

## Get Stub Networks Groups for Specific Country

``` python
# Go to the split_as_stubs.py file
# Change the main function from main() to main1()

if __name__ == '__main__':
    # main()
    main1()
```

Generate a new stub group file:

``` sh
$ ./split_as_stubs.py 20181201.as-rel.txt 20150801.as2types.txt as-country.txt > us-stubs.txt
```

## Run Group Simulation

``` sh
# Read group 0 in stubs.txt for global simulation
$ ./bubblecast_group_sim.py 20181201.as-rel.txt stubs.txt 0

# Read group 0 in stubs.txt for global simulation with counter=250
$ ./bubblecast_group_sim.py 20181201.as-rel.txt stubs.txt 0 250

# Read group 0 in stubs.txt for US topology simulation
$ ./bubblecast_usgroup_sim.py 20181201.as-rel.txt as-country.txt stubs.txt 0

# Read group 0 in stubs.txt for global simulation with counter=250
$ ./bubblecast_usgroup_sim.py 20181201.as-rel.txt as-country.txt stubs.txt 0 250
```

## Run Batch of Group Simulation

``` sh
$ ./start_sim.sh 20181201.as-rel.txt stubs.txt 0 99

$ ./start_us_sim.sh 20181201.as-rel.txt as-country.txt us-stubs.txt 0 99
```

# Analysis of Internet Traffic

## Prepare

``` sh
$ pip3 install pyasn --pre --user
$ pyasn_util_download.py --latest
$ ls
rib.20190116.1600.bz2

$ pyasn_util_convert.py --single rib.20190016.1600.bz2 ipasn.20190116.1600.dat
```

## Map IP to ASN

``` sh
$ ./extract-asn-port-vol.sh caida/passive-2016/equinix-chicago/
```

## Process Traffic Volume Statistics by Port

``` sh
# Statistics for Each AS
$ ./port_stats.py caida/passive-2016/equinix-chicago/20160121-130000.UTC 1

# Summary of Statistics
$ ./port_stats.py caida/passive-2016/equinix-chicago/20160121-130000.UTC 2
```
