import re

old_file ='/Users/zq/work/node.log.2023-06-03.43'
new_file = '/Users/zq/work/temp.txt'

def get_file(filename):
    try: 
        with open(filename, encoding='utf-8') as file_obj:
            lines = file_obj.read()
        get_key(lines)
    except UnicodeDecodeError:
        print(filename)

def get_key(lines):
    data = {}
    res1 = re.findall('shopMapIdStock=\d{1,}',lines)
    for iterating_var in res1:
        data.setdefault(iterating_var)
    write_file(data)

def write_file(data):
    new_message=''
    for key,value in data.items():
        new_message=key+'\n'
        file = open(new_file, 'a+',encoding='utf-8')
        file.write(new_message)
        file.close()

if __name__ == "__main__":
    get_file(old_file)