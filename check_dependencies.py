import subprocess
import sys


def check_lib_krb5():
    try:
        result = subprocess.run(
            ["dpkg", "-s", "libkrb5-dev"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        if result.returncode == 0:
            print("libkrb5-dev is installed.")
        else:
            print("libkrb5-dev is not installed.")
            sys.exit(1)
    except subprocess.CalledProcessError:
        print("libkrb5-dev is not installed. Run 'sudo apt install libkrb5-dev'.")
        sys.exit(1)


if __name__ == "__main__":
    check_lib_krb5()
