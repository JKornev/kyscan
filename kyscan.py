import q3net
import datetime
import concurrent.futures
import threading
import argparse

quake3_frequent_ports = [
    1582, 1838, 4399, 4654, 4910, 4921, 5422, 5934, 6190, 6702, 
    6989, 7700, 7726, 9000, 9262, 10542, 10798, 11777, 11791, 11801, 
    11807, 11810, 11815, 11822, 11837, 11853, 11878, 11900, 15150, 18235, 
    18737, 19296, 20850, 21294, 21775, 22062, 24077, 24096, 24444, 24878, 
    26414, 26926, 27000, 27666, 27694, 27905, 27950, 27960, 27961, 27962, 
    27963, 27964, 27965, 27966, 27967, 27968, 27969, 27970, 27971, 27972, 
    27973, 27974, 27975, 27976, 27977, 27980, 27985, 27986, 27990, 27992, 
    27999, 28000, 28010, 28015, 28020, 28030, 28200, 28206, 28240, 28258, 
    28452, 28462, 28491, 28492, 28543, 28700, 28718, 28799, 28960, 28969, 
    28971, 28972, 28973, 28974, 29000, 29005, 29010, 29030, 29040, 29230, 
    29711, 29734, 29742, 29777, 29961, 29965, 29966, 29968, 29970, 29979, 
    29980, 29992, 29996, 29998, 30001, 30010, 30530, 32296
]

qwfwd_frequent_ports = [ 12345, 29999, 30000, 30001, 30002, 30003, 30004, 30005 ]

class logger:
    _last_message_len : int = 0
    _message_overwritten : bool = False
    _lock = threading.Lock()

    def __del__(self):
        # If the last message doesn't have new line character in the end -> lets put it
        if self._message_overwritten:
            print("\n", end='')
    
    def write(self, message):
        with self._lock:
            self._cleanup_line(message)
            print(f"\r{message}")
            self._message_overwritten = False
            self._last_message_len = 0

    def overwrite(self, message):
        with self._lock:
            self._cleanup_line(message)
            print(f"\r{message}", end= '')
            self._message_overwritten = True
            self._last_message_len = len(message)
 
    def _cleanup_line(self, message):
        if not self._message_overwritten:
            return

        delta = self._last_message_len - len(message)
        if 0 >= delta:
            # nothing to cleanup
            return

        # Cleanup previous message by spaces
        print(f'\r'.ljust(self._last_message_len + 1, ' '), end= '')


def get_userinfo_field(userinfo, key, default= "N\\A"):
    if key in userinfo.keys():
        return userinfo[key]
    return default

def check_quake3_port(host, port):
    log.overwrite(f"Scanning port {host}:{port}")

    connection = q3net.connection(host, port)
    try:
        return connection.request(q3net.get_info_request(), timeout= args.timeout)
    except:
        pass
    finally:
        connection.terminate()
    return None

def check_qwfwd_port(host, port):
    log.overwrite(f"Scanning proxy {host}:{port}")
    connection = q3net.connection(host, port)
    try:
        # Lets check QWFWD proxy port via fast 'pingstatus' request
        # https://github.com/QW-Group/qwfwd/blob/202646204866213754d6f72d7730c9113eb36725/src/svc.c#L459
        response = connection.request(q3net.command_request(b"pingstatus", None, False), timeout= args.timeout) 
        # Response pattern (header) \xFF\xFF\xFF\xFFn
        if response and response.data[0] == 'n':
            return response
    except:
        pass
    finally:
        connection.terminate()
    return None

def scan_ports():    
    host = args.host
    started = datetime.datetime.now()

    with concurrent.futures.ThreadPoolExecutor(args.pool) as pool:

        if args.mode == "fast" or args.mode == "full":
            log.write("Fast scanning has been started")
            # 1. Scan frequent quake 3 ports
            futures = { pool.submit(check_quake3_port, host, port): port for port in quake3_frequent_ports }
            for future in concurrent.futures.as_completed(futures):
                response = future.result()
                if response:
                    print_server(host, futures[future], response.data)

            # 2. Scan frequent qwfwd ports
            futures = { pool.submit(check_qwfwd_port, host, port): port for port in qwfwd_frequent_ports }
            for future in concurrent.futures.as_completed(futures):
                if future.result():
                    print_proxy(host, futures[future])

        if args.mode == "full":
            log.write("Full scanning has been started")
            # 3. Scan all other quake3 ports
            futures = { pool.submit(check_quake3_port, host, port): port for port in range(1, 65535) }
            for future in concurrent.futures.as_completed(futures):
                response = future.result()
                if response:
                    print_server(host, futures[future], response.data)

            # 4. Scan all other qwfwd ports
            futures = { pool.submit(check_qwfwd_port, host, port): port for port in range(1, 65535) }
            for future in concurrent.futures.as_completed(futures):
                if future.result():
                    print_proxy(host, futures[future])

        if args.mode == "range":
            log.write(f"Range scanning ({args.start} - {args.end}) has been started")
            # 3. Scan all other quake3 ports
            futures = { pool.submit(check_quake3_port, host, port): port for port in range(args.start, args.end + 1) }
            for future in concurrent.futures.as_completed(futures):
                response = future.result()
                if response:
                    print_server(host, futures[future], response.data)

            # 4. Scan all other qwfwd ports
            if args.with_proxy:
                futures = { pool.submit(check_qwfwd_port, host, port): port for port in range(args.start, args.end + 1) }
                for future in concurrent.futures.as_completed(futures):
                    if future.result():
                        print_proxy(host, futures[future])

    # 5. Complete
    delta  = datetime.datetime.now() - started
    log.write(f"Completed in {delta}")

def print_server(host, port, userinfo):
    game = get_userinfo_field(userinfo, "game")
    protocol = get_userinfo_field(userinfo, "protocol")
    hostname = get_userinfo_field(userinfo, "hostname")
    log.write(f" server: {host}:{port}, game: {game.upper()}, protocol: {protocol}, hostname: {hostname}")
    log.overwrite("Scanning ...")

def print_proxy(host, port):
    log.write(f" proxy: {host}:{port}")
    log.overwrite("Scanning ...")

def parse_arguments():
    parser = argparse.ArgumentParser(
        add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        prog= "kyscan",
        description= "Quake III port scanner",
        epilog= '''examples:
  kyscan --pool 512 --timeout 4 full aim.pm - full scan with 512 threads and timeout 4.0 seconds
  kyscan fast aim.pm                        - fast scan with default parameters
  kyscan -t 5 range 27960 27970 aim.pm      - scan ports range 27960 - 27970 with timeout 5.0 seconds
  '''
    )

    # Options arguments
    options = parser.add_argument_group("options")
    options.add_argument("-p", "--pool", metavar= "<threads>", type= int, default= 128, help= "set amount of threads in the threads pool (default: 128)")
    options.add_argument("-t", "--timeout", metavar= "<seconds>", type= float, default= 3.0, help= "set the port query timeout (default: 3.0)")

    # Modes
    sub_parser = parser.add_subparsers( title= "modes")
    fast = sub_parser.add_parser("fast", help= "fast scan using most frequent ports")
    fast.set_defaults(mode= "fast")

    full = sub_parser.add_parser("full", help= "full scan for a whole range of the ports 1 - 65535")
    full.set_defaults(mode= "full")

    range = sub_parser.add_parser("range", help= "scan the specific ports range")
    range.add_argument("start", metavar= "<start>", type= int)
    range.add_argument("end", metavar= "<end>", type= int)
    range.add_argument("-wp", "--with-proxy", action= "store_true")
    range.set_defaults(mode= "range")

    # Required
    required = parser.add_argument_group("required")
    required.add_argument("host", help= "host to be scanned")

    return parser.parse_args()

if __name__ == '__main__':
    log = logger()
    args = parse_arguments()
    scan_ports()
