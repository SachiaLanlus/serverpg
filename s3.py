from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
import os
import cgi
import subprocess
import sys
import pyqrcode
from pyunpack import Archive
import traceback

server_base_path='public/'
game_base_path='game/'
archive_base_path='archive/'
secret=''

def parse(qmap):
    qmap=[list(x) for x in qmap.split('\n')]
    output=''
    tmp=''
    pattern=''
    for i in range(4,len(qmap)-4,2):
        tmp=''
        for j in range(4,len(qmap[i])-4):
            pattern=qmap[i][j]+qmap[i+1][j]
            if(pattern=='00'):
                tmp+=' '
            elif(pattern=='01'):
                tmp+='▄'
            elif(pattern=='10'):
                tmp+='▀'
            elif(pattern=='11'):
                tmp+='█'
            else:
                pass
        output+=tmp+'\n'
    return output

#https://stackoverflow.com/questions/8529265/
#google-authenticator-implementation-in-python
import hmac, base64, struct, hashlib, time

def get_hotp_token(secret, intervals_no):
    key = base64.b32decode(secret, True)
    msg = struct.pack(">Q", intervals_no)
    h = hmac.new(key, msg, hashlib.sha1).digest()
    #o = ord(h[19]) & 15
    o = h[19] & 15
    h = (struct.unpack(">I", h[o:o+4])[0] & 0x7fffffff) % 1000000
    return h

def get_totp_token(secret):
    return get_hotp_token(secret, intervals_no=int(time.time())//30)
###############################################

class PostHandler(SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200, 'ok')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, HEAD')
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        return
        
    def do_POST(self):
        archive_type='null'
        parsed_ts=time.time()
        try:
            ctype,pdict=cgi.parse_header(self.headers.get('Content-Type'))
            pdict['boundary']=bytes(pdict['boundary'],'utf-8')
            content_len = int(self.headers.get('Content-length'))
            pdict['CONTENT-LENGTH'] = content_len
            if(ctype=='multipart/form-data'):
                fields=cgi.parse_multipart(self.rfile, pdict)
                archive_name=fields.get('archive_name')[0]
                archive_file=fields.get('archive_file')[0]
                archive_link=fields.get('archive_link')[0]
                archive_format=fields.get('archive_format')[0]
                htop=fields.get('htop_token')[0]
                if(int(htop.strip())!=get_hotp_token(secret, intervals_no=int(parsed_ts)//30)):
                    print('htop token mismatch')
                    print(htop.strip()+' vs '+str(get_hotp_token(secret, intervals_no=int(parsed_ts)//30)))
                    self.wfile.write(bytes('htop token mismatch','utf-8'))
                    self.connection.shutdown(1)
                    return
                if(len(archive_file)>0):
                    assert archive_type=='null'
                    archive_type='file'
                if(len(archive_link)>0):
                    assert archive_type=='null'
                    archive_type='link'
        except AssertionError:
            print('archive_type has multiple value')
            traceback.print_exc()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=UTF-8')
            self.end_headers()
            self.wfile.write(bytes('Do NOT upload archive and link at the same time.','utf-8'))
            self.connection.shutdown(1)
            return
        except:
            print('Process request error')
            traceback.print_exc()
            self.wfile.write(bytes('Error','utf-8'))
            self.connection.shutdown(1)
            return
        print('archive_type='+archive_type)
        if(archive_type=='file'):
            with open(archive_base_path+archive_name+'.'+archive_format,'wb') as f:
                f.write(archive_file)
                del archive_file
        elif(archive_type=='link'):
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=UTF-8')
            self.end_headers()
            self.wfile.write(bytes('Request sent.','utf-8'))
            self.connection.shutdown(1)
            try:
                p=subprocess.Popen(['wget','-q','-O',archive_base_path+archive_name+'.'+archive_format,archive_link],stdout=open(os.devnull, 'w'),stderr=subprocess.STDOUT)
                p.wait()
            except:
                print('wget error')
                traceback.print_exc()
                return
        else:
            print('do nothing')
            return
        try:
            #os.makedirs(game_base_path+archive_name,exist_ok=True)
            Archive(archive_base_path+archive_name+'.'+archive_format).extractall(game_base_path+archive_name,auto_create_dir=True)
        except:
            print('unzip/unrar error')
            traceback.print_exc()
            return
        print('finish')
        self.send_response(303)
        self.send_header('Location', 'game')
        self.end_headers()
        return


def StartServer():
    global secret
    os.chdir(server_base_path)
    os.makedirs('game',exist_ok=True)
    os.makedirs('archive',exist_ok=True)
    sever = ThreadingHTTPServer(("",int(os.environ.get('PORT',9999))),PostHandler)
    print('ready')
    print()
    passphrase=os.environ.get('PASSPHRASE',str(int(time.time())))
    passphrase=passphrase[:10]
    passphrase=' '*(len(passphrase)-10)+passphrase
    secret=base64.b32encode(passphrase.encode('ascii')).decode('ascii')
    uid='me'
    mark='serverpg'
    qr=pyqrcode.create('otpauth://totp/'+uid+'?secret='+secret+'&issuer='+mark)
    secret_path=hashlib.blake2b(bytes(secret,'ascii')+bytes(str(time.time()),'ascii'),digest_size=16).hexdigest()+'.svg'
    secret_url='/'+secret_path
    print(secret_url)
    qr.svg(secret_path, scale=8)
    #print(parse(qr.text()))
    sever.serve_forever()

if __name__=='__main__':
    StartServer()
