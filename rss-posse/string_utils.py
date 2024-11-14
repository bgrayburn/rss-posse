def word_count(string: str):
    words = string.split()
    return len(words)

def removeSpaces(string: str):
    return ''.join(string.split(' '))