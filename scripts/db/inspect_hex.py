
import binascii

def check_file(filename):
    with open(filename, 'rb') as f:
        content = f.read()
    
    lines = content.split(b'\n')
    
    # 0-indexed, so line 57 is index 56
    if len(lines) > 56:
        print(f"Line 57 (hex): {binascii.hexlify(lines[56])}")
        print(f"Line 57 (utf8): {lines[56].decode('utf-8', errors='replace')}")
    else:
        print("File has fewer than 57 lines")

if __name__ == "__main__":
    check_file('C:/Users/Gianluca/Documents/TheSentient/frontend/src/components/BotConfigModal.vue')
