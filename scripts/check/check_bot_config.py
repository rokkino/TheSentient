
def check_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Simple check for balanced braces in template (ignoring script for now, just checking template lines 1-100)
    # This is a naive check but might catch obvious unclosed things.
    
    stack = []
    in_template = True
    
    for i, line in enumerate(lines):
        if '</template>' in line:
            in_template = False
            break
            
        # Remove simple attributes to reduce noise (naive)
        # We are looking for unclosed quotes mainly
        
        # Check quotes
        sq = 0
        dq = 0
        for char in line:
            if char == "'": sq += 1
            if char == '"': dq += 1
            
        # This is too naive because of escaping and content.
        # Let's focused on {{ }} matching and unclosed tags.
        pass

    # Let's try to match {{ and }}
    content = "".join(lines[:100])
    
    # Check for unclosed tags?
    # Or maybe just print the lines around 96 and 57 with clear representation of invisible chars
    print(f"Line 57: {repr(lines[56])}")
    print(f"Line 96: {repr(lines[95])}")

if __name__ == "__main__":
    check_file('C:/Users/Gianluca/Documents/TheSentient/frontend/src/components/BotConfigModal.vue')
