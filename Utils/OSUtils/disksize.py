import os
import argparse
from collections import defaultdict

def get_size(path):
    """Returns the total size of a directory or file in bytes."""
    if os.path.isfile(path):
        return os.path.getsize(path)
    total_size = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total_size += os.path.getsize(fp)
    return total_size

def find_largest_files_and_folders(start_path, top_n=10):
    """Finds the largest files and directories in a given path."""
    size_map = defaultdict(int)
    
    for root, dirs, files in os.walk(start_path):
        for name in dirs + files:
            full_path = os.path.join(root, name)
            try:
                size_map[full_path] = get_size(full_path)
            except Exception as e:
                print(f"Error accessing {full_path}: {e}")
    
    sorted_items = sorted(size_map.items(), key=lambda x: x[1], reverse=True)[:top_n]
    
    print(f"Top {top_n} largest files and directories in '{start_path}':")
    for path, size in sorted_items:
        print(f"{size / (1024*1024):.2f} MB - {path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find the largest files and directories in a given location.")
    parser.add_argument("path", help="The path to scan (e.g., C:\\ or C:\\Users\\Name)")
    parser.add_argument("-n", "--top", type=int, default=10, help="Number of largest items to display")
    args = parser.parse_args()
    
    find_largest_files_and_folders(args.path, args.top)