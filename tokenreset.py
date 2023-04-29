from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
def token(email,seconds):
    s=Serializer('*67@ouihfg',seconds)
    return s.dumps({'user':email}).decode('utf-8')
    
