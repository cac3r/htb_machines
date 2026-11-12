s = "<text>"
print(''.join(f"\\u{ord(c):04x}" for c in s))
