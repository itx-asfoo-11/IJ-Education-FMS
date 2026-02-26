import os
import shutil

# This script is intended to be run to save the uploaded image to the static folder.
# Since the image is passed in the prompt, I will simulate saving it if I can't reach it directly, 
# but usually, I should be able to see where it's stored.
# For now, I'll prepare the directory and wait to see if I can find the path.
# Actually, I'll use the placeholder if I can't find it, but the user said "Replace purple 'F' circle with uploaded image".

static_dir = r"c:\Users\umartech\OneDrive\Desktop\F_M_S\fees\static\fees\img"
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

print(f"Directory {static_dir} ensured.")
