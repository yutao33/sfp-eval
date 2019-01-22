#!/bin/bash

curl -sSL http://bgp.potaroo.net/cidr/autnums.html | pup 'pre text{}' > as-country-raw.txt
./filter_autnums.py as-country-raw.txt > as-country.txt
