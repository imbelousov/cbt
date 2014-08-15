import client

def main():
    c = client.Client()
    c.append("data\\2.torrent", "data\\download")
    c.stop()
    c.start()

if __name__ == "__main__":
    main()