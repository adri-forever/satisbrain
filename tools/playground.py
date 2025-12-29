from airium import Airium

# for more complex structures, it actually requires @contextmanager
def ftest(a: Airium, text) -> Airium:
    a.div(_t='ahem', klass='oi')
    return a.div(_t=text, klass='aha')
    

if __name__ == '__main__':
    a = Airium()
    a.div(_t='yoyo')
    
    with ftest(a, '123'):
        a.div(_t='vivalalgerie', klass='aac')
        
    print(a)