import re
st = "FF 문제가 있습니다. 어떻게 고치는 지?  "
word1 = " ".join(re.findall("[a-zA-Z0-9]+", st))
print(word1)