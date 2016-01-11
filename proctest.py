import subprocess

class SafePopen(subprocess.Popen):
    def safe_kill(self):
        self.kill()
        self.wait()

if __name__ == "__main__":
    proc = SafePopen("notepad.exe")
    raw_input("press any key to end app...")
    proc.safe_kill()