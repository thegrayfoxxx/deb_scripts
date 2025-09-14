from scripts.run import run_interactive_script


def main():
    run_interactive_script()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Exiting...")
