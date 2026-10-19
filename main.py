import argparse

from network.setup import run

def cache_check(val):
    val = int(val)
    if val <= 0:
        raise argparse.ArgumentTypeError(
            "Cache size must be greater than zero (0)"
        )
    return val

def appendfsync_check(val):
    if val not in ("always", "everysec", "no"):
        raise argparse.ArgumentTypeError(
            "appendfsync time must be either always, everysec, or no"
        )
    return val

def main():

    parser = argparse.ArgumentParser(
        description="Run the Kelvin key-value server.",
    )

    parser.add_argument(
        "--ip",
        type=str,
        default="127.0.0.1",
        help="Override preset ip"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=6379,
        help="Override preset port"
    )

    parser.add_argument(
        "--appendfsync",
        nargs="?",
        default="no",
        type=appendfsync_check,
        metavar="SIZE",
        help=(
            "Enable appending to aof, if so what at what rate"
            "(default: no)"
        ),
    )


    parser.add_argument(
        "--cache",
        nargs="?",
        const=100,
        default=None,
        type=cache_check,
        metavar="SIZE",
        help=(
            "Enable caching with a maximum size "
            "(default: 100)"
        ),
    )

    args = parser.parse_args()
    run(ip=args.ip, port=args.port, cache_size=args.cache, aof_type=args.appendfsync)

if __name__ == "__main__":
    print("Kelvin Starting")
    main()