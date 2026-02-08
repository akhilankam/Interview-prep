# #Given the list ['cat', 'dog', 'lion', 'cat', 'lion', 'dog', 'hen', 'cat', 'dog'], write a
# # Python program to find which string occurs the maximum number of times."

# | Expression      | What it gives / means                                                                    |
# | --------------- | ---------------------------------------------------------------------------------------- |
# | `freq`          | Iterates over **keys only**                                                              |
# | `freq.keys()`   | Iterates over **keys only**                                                              |
# | `freq.values()` | Iterates over **values only**                                                            |
# | `freq.items()`  | Iterates over **(key, value)** pairs ✅                                                   |
# | `key=freq.get`  | Tells functions like `max()` / `min()` to **compare dictionary keys using their values** |


from collections import Counter
lst = ['cat', 'dog', 'lion', 'cat', 'lion', 'dog', 'hen', 'cat', 'dog']
freq = {}

for i in lst:
    if i in freq:
        freq[i]+=1
    else:
        freq[i]=1
apex = dict(Counter(lst))
print(apex)
print(freq)
print(max(freq, key=freq.get))
max_freq= max(freq.values())
print(max_freq)
result = [k for k,v in freq.items() if v==max_freq]
print(result)

# list = ['cat', 'dog', 'lion', 'cat', 'lion', 'dog', 'hen', 'cat', 'dog']
# count = 0
# for i in list:
#     for j in list:
#         if i==j:
#             [j]==lenght(list-1)
#             count =count+1
#     print(count )

# Given a list of integers a = [12, 21, 38, 42, 56, 69, 16, 21], 
# write a Python program to create a new list that contains all elements of a except the number 21

a = [12, 21, 38, 42, 56, 69, 16, 21]
b=[]
for i in a:
    if i!=21:
        b.append(i)

print(b)



# for i in a:
#     if i==21:
#         a.(i)
    
# print(a)




# Write a function that checks if a file exists in a given directory,
#  and if it does, prints the last 10 lines of the file.

# path = C:\\Users\akhil\Desktop
# file = "test.py"

# file_check = os.path.exists(path,file)

# print(file_check)

# last_lines = os.path.f

from collections import deque
import os 

def print_last_10_lines(directory, filename):
    file_path = os.path.join(directory,filename)

    if not os.path.isfile(file_path):
        print("file doesn't exist")
        return

    with open(file_path,'r') as file:
        for line in deque(file, maxlen=10):
            print(line.rstrip())


print_last_10_lines(r"C:\Users\akhil\Desktop\DevOps\workplace", "EKS_CLUSTER_DELETION_GUIDE.md")


# | Method     | Removes               |
# | ---------- | --------------------- |
# | `rstrip()` | Right-side whitespace |
# | `lstrip()` | Left-side whitespace  |
# | `strip()`  | Both sides            |
# Example:
# text = "   hi   "
# print(text.strip())   # "hi"
# print(text.rstrip())  # "   hi"
# print(text.lstrip())  # "hi   "
