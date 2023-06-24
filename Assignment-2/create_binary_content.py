import os

file_path = 'binary_file.bin'
file_size = 256 * 1024  # 256 KB

# Generate random binary data of the desired size
data = os.urandom(file_size)

# Write the binary data to the file
with open(file_path, 'wb') as file:
    file.write(data)

print(f'Binary file of size {file_size} bytes created successfully.')