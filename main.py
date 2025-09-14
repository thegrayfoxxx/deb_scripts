from scripts.bbr import BBR
from scripts.docker import Docker
from scripts.fail2ban import Fail2Ban
from scripts.uv import UV


def main():
    print("Hello from deb-scripts!")
    user_input = str(input("Exit - 0\nBBR - 1\nDocker - 2\nFail2Ban - 3\nUV - 4\n"))
    match user_input:
        case "0":
            exit()
        case "1":
            bbr = BBR()
            bbr.interactive_run()
        case "2":
            docker = Docker()
            docker.interactive_run()
        case "3":
            fail2ban = Fail2Ban()
            fail2ban.interactive_run()
        case "4":
            uv = UV()
            uv.interactive_run()
        case _:
            print("Invalid input")
            main()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Exiting...")
