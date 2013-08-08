#!/user/bin/python27
from pstats import Stats
from time import sleep
import sys

output = open(sys.argv[1]+'.stats', 'w')
statistics = Stats(sys.argv[1], stream=output)

statistics.print_stats()
sleep(5)