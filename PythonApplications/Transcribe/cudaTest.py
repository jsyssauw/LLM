import torch
print("PyTorch version:", torch.__version__)
print("CUDA available:", torch.cuda.is_available())
print("CUDA device count:", torch.cuda.device_count())
print("CUDA device name:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "No GPU found")
print("CUDA version:", torch.version.cuda if torch.cuda.is_available() else "No CUDA")


print(torch.version.cuda)  # Should match your installed CUDA version (e.g., 12.8)
print(torch.backends.cudnn.version())  # Should return a valid CuDNN version
