import sys

import client.client


def main():
    c = client.client()
    c.open_from_file(sys.argv[1])
    c.set_download_path(sys.argv[2])
    c.start()
    try:
        #client.client.main_loop()
        pass
    except KeyboardInterrupt:
        pass
    c.stop()


if __name__ == "__main__":
    main()
