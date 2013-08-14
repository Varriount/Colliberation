#!/user/bin/python27

import os
import sys
# Hack to allow us to import external libraries
__file__ = os.path.normpath(os.path.abspath(__file__))
__path__ = os.path.dirname(__file__)
libs_path = os.path.join(__path__, 'libs')
if libs_path not in sys.path:
    sys.path.insert(0, libs_path)

from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ServerEndpoint
from colliberation.server.factory import CollabServerFactory
from twisted.manhole.telnet import ShellFactory
import traceback
import cProfile, pstats, io
prof = None
def main():
    port = 6687
    server_factory = CollabServerFactory()
    shell_factory = ShellFactory()

    server_endpoint = TCP4ServerEndpoint(reactor, port)

    shell_factory.username = ""
    shell_factory.password = ""
    shell_factory.namespace['factory'] = server_factory

    server_connection = server_endpoint.listen(server_factory)
    shell_connection = reactor.listenTCP(6684, shell_factory)
    #profiler = cProfile.Profile()
    #profiler.enable()
    reactor.run()
    #profiler.disable()
    #profiler.dump_stats('server_stats.prof')
    #globals()['prof'] = profiler

try:
    main()
except Exception:
    import traceback
    print(traceback.format_exc())
    raw_input()
else:
    import time
    time.sleep(30)
