import hashlib
import base64

class FileHander():
    def __init__(self,f):
        self.f = f

    def hash(self):
        return hashlib.sha1(self.f).hexdigest()

    def base64(self):
        return base64.b64encode(self.f)



#test
'''
with open ("cover.png",'rb') as f:
    image = f.read()

a = FileHander(image)
print(type(a.base64()))
'''