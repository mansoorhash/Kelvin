import argparse

from network.setup import run

def cache_check(val):
    val = int(val)
    if val <= 0:
        raise argparse.ArgumentTypeError(
            "Cache size must be greater than zero (0)"
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
    run(ip=args.ip, port=args.port, cache_size=args.cache)

if __name__ == "__main__":
    print("Kelvin Starting")
    main()