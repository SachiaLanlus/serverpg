from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
import os
import cgi
import subprocess
import sys

server_base_path='public/'
game_base_path='game/'
archive_base_path='archive/'

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
        try:
            ctype,pdict=cgi.parse_header(self.headers.get('Content-Type'))
            pdict['boundary']=bytes(pdict['boundary'],'utf-8')
            content_len = int(self.headers.get('Content-length'))
            pdict['CONTENT-LENGTH'] = content_len
            if(ctype=='multipart/form-data'):
                fields=cgi.parse_multipart(self.rfile, pdict)
                archive_name=fields.get('archive_name')[0]
                archive_file=fields.get('archive_file')
                archive_link=fields.get('archive_link')
                if(len(archive_file)>0):
                    archive_file=archive_file[0]
                    archive_type='file'
                if(len(archive_link)>0):
                    archive_link=archive_link[0]
                    archive_type='link'
        except:
            print('Process request error')
            self.wfile.write(bytes('Error','utf-8'))
            self.connection.shutdown(1)
            return
        if(archive_type=='file'):
            with open(archive_base_path+archive_name+'.zip','wb') as f:
                f.write(archive_file)
                del archive_file
        elif(archive_type=='link'):
            stdout = sys.stdout
            sys.stdout = open(os.devnull, 'w')
            p=subprocess.Popen(['wget','-O',archive_base_path+archive_name+'.zip',archive_link])
            p.wait()
            sys.stdout=stdout
        else:
            return
        try:
            stdout = sys.stdout
            sys.stdout = open(os.devnull, 'w')
            #p=subprocess.Popen(['wsl','"unzip '+archive_base_path+archive_name+'.zip -d '+game_base_path+archive_name+'"'])
            p=subprocess.Popen(['unzip',archive_base_path+archive_name+'.zip','-d',game_base_path+archive_name])
            p.wait()
            sys.stdout=stdout
        except:
            print('unzip error')
            return
        self.send_response(303)
        self.send_header('Location', 'game')
        self.end_headers()
        return


def StartServer():
    os.chdir(server_base_path)
    os.makedirs('game',exist_ok=True)
    os.makedirs('archive',exist_ok=True)
    sever = ThreadingHTTPServer(("",int(os.environ.get('PORT',9999))),PostHandler)
    print('ready')
    sever.serve_forever()

if __name__=='__main__':
    StartServer()
