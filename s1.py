from http.server import SimpleHTTPRequestHandler,HTTPServer
import json
import os
import time
import datetime
import cgi
from urllib.parse import unquote
import subprocess

class PostHandler(SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200, 'ok')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, HEAD')
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        return
        
    def do_POST(self):
        self.send_response(303)
        self.send_header('Location', 'list.html')
        self.end_headers()
        try:
            ctype,pdict=cgi.parse_header(self.headers.get('Content-Type'))
            pdict['boundary']=bytes(pdict['boundary'],'utf-8')
            content_len = int(self.headers.get('Content-length'))
            pdict['CONTENT-LENGTH'] = content_len
            if(ctype=='multipart/form-data'):
                fields=cgi.parse_multipart(self.rfile, pdict)
                archive_name=fields.get('archive_name')[0].decode('utf-8')
                archive_file=fields.get('archive_file')[0]
        except:
            print('Process request error')
            raise
            self.wfile.write(bytes('Error','utf-8'))
            self.connection.shutdown(1)
            return
        with open(archive_name+'.zip','wb') as f:
            f.write(archive_file)
            f.close()
            del archive_file
        try:
            p=subprocess.Popen(['unzip',archive_name+'.zip','-d','game/'+archive_name])
            p.wait()
        except:
            print('unzip error')
            return
        time.sleep(1)
        try:
            game_list=os.listdir('game')
            s='<!DOCTYPE html><html><head><link rel="icon" href="https://serverpg.herokuapp.com/favicon.ico"><title>Game List</title></head>'
            for e in game_list:
                s+=datetime.datetime.fromtimestamp(os.path.getctime(e+'.zip')).strftime('%Y/%m/%d-%H:%M:%S')+' '+str(int(os.path.getsize(e+'.zip')/10485.76)/100)+'MB<br><a href="game/'+e+'" target="_blank" rel="noopener noreferrer">'+e+'</a><br>'
            with open('list.html','w',encoding='utf-8') as f:
                f.write(s)
        except:
            print('list game error')
            return
        return


def StartServer():
    os.makedirs('game',exist_ok=True)
    sever = HTTPServer(("",int(os.environ.get('PORT',9999))),PostHandler)
    #sever = HTTPServer(("",9999),PostHandler)
    #sever.socket = ssl.wrap_socket (sever.socket, certfile='server.pem', server_side=True)
    print('ready')
    sever.serve_forever()

if __name__=='__main__':
    StartServer()
