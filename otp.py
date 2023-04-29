import random
def genotp():
    upc=[chr(i) for i in range(ord('A'),ord('Z')+1)]
    lwc=[chr(i) for i in range(ord('a'),ord('z')+1)]
    otp=''
    for i in range(2):
        otp+=random.choice(upc)
        otp+=str(random.randint(0,9))
        otp+=random.choice(lwc)
    return otp