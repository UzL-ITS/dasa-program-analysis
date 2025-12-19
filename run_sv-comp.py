import base64
import glob
import sys
import os
import subprocess
from contextlib import contextmanager

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
WITNESS_PATH = os.path.join(SCRIPT_DIR, 'libs/WitnessCreator/build/libs/WitnessCreator.jar')
LIB_DIR = os.path.join(SCRIPT_DIR, 'libs/')
for wheel in glob.glob(os.path.join(LIB_DIR, "*.whl")):
    sys.path.insert(0, wheel)

import test # this has to happen after all wheels are loaded

def main():
    start_file = "Main.main.json"
    try:
        output = None
        res = test.main(start_file, None, None, auto_detect_start_end=True,
                        test_dir="SUT/", use_sv_helpers=False, test_class="Main", return_successfull_output=True,
                        num_iterations=500, verbose=False)
        if type(res) == tuple:
            res, output = res
        match res:
            case test.STATE_CORRECT:
                print(f'DASA_VERDICT: VIOLATION')
            case test.STATE_NO_START_NODES_FOUND | test.STATE_NO_END_NODES_FOUND:
                print('No start/end nodes found')
                res = subprocess.run(["java", "-cp", f"SUT/", "-ea", "Main"], capture_output=True)
                if res.returncode != 0:
                    print("----------- Output of the test execution -----------")
                    print(res.stdout.decode("utf-8"))
                    print(res.stderr.decode("utf-8"))
                    print("----------------------------------------------------")
                    if "java.lang.AssertionError" in res.stderr.decode("utf-8"):
                        print("DASA_VERDICT: VIOLATION")
                        output = res.stdout.decode("utf-8")
                    else:
                        print("DASA_VERDICT: UNKNOWN")
                else:
                    print("DASA_VERDICT: UNKNOWN")
            case _:
                print(f'DASA_VERDICT: UNKNOWN')
        if output is not None:
            witnesses = extract_markers(output, '[WITNESS]')
            enc = base64.b64encode(("\n".join(witnesses)).encode())
            cmd = ['java', '-jar', WITNESS_PATH, enc, os.path.join(SCRIPT_DIR, 'SUT')]
            print(cmd)
            with pushd(os.path.join(SCRIPT_DIR, 'libs/WitnessCreator/')):
                res = subprocess.run(cmd, capture_output=True)
            if res.returncode != 0:
                print("EXCEPTION WHILE CREATING WITNESS")
                print(res.stderr.decode("utf-8"))
            else:
                print("WITNESS CREATED")
            print(res.stdout.decode("utf-8"))
    except Exception as e:
        print(f'DASA_VERDICT: UNKNOWN')
        raise e

def extract_markers(out, marker):
    res = []
    for line in out.split("\n"):
        if marker in line:
            res.append(line)
    return res

@contextmanager
def pushd(dirname):
    """Context manager to temporarily change the working directory."""
    original_dir = os.getcwd()
    os.chdir(dirname)
    try:
        yield
    finally:
        os.chdir(original_dir)

if __name__ == '__main__':
    main()