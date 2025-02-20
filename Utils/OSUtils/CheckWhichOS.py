import os
import platform

system_name = platform.system()
if system_name == "Windows":
    print("Running on Windows")
    downloads_dir = os.path.join(os.environ["USERPROFILE"], "Downloads")
    print(downloads_dir)
elif system_name == "Darwin":
    print("Running on macOS")
    downloads_dir = os.path.join(os.environ["HOME"], "Downloads")
    print(downloads_dir)
elif system_name == "Linux":
    print("Running on Linux")
    downloads_dir = os.path.join(os.environ["HOME"], "Downloads")
    print(downloads_dir)
