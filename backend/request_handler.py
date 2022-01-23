import sys
import time
import threading
import requests
import json

from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

API_ENDPOINT = 'https://api.hgbrasil.com/finance/stock_price?key=70b8862b&symbol='

'''
    Classe principal, manipula em uma thread separada cada requisição que chega ao servidor.
    A cada requisição, a classe processa os parâmetros informados, busca os dados na API externa, filtra e retorna uma lista de resultados como resposta da requisição.
'''
class RequestHandler(SimpleHTTPRequestHandler):
    
    '''
        Trata um erro 404
    '''
    def handle_endpoint_error(self):
        self.send_error(404, "Path does not exists.")
        sys.exit()

    '''
        Valida a requisição recebida, verificando se ela contém o endpoint correto.
    '''
    def is_valid(self):
        start = self.path.find("/")
        end = self.path.find("?")
        endpoint = self.path[start:end]
    
        if endpoint != '/active_price':
            return False
        return True

    '''
        Extrai os parâmetros da requisição, caso esta seja válida.
    '''
    def parse_request_parameters(self):
        start = self.path.find('=') + 1
        end = self.path.find('&')
        if end == -1:
            end = len(self.path)
        query = self.path[start:end]
        codes = query.split(',')
        return codes

    '''
        Trata um erro na chamda à API externa.
    '''
    def handle_api_error(self):
        self.send_error(500, "Internal Server Error")
        sys.exit()

    '''
        Extrai os parâmetros desejados da resposta da API externa.
    '''
    def extract_values(self, request):
        response = json.loads(request.text)
        result_list = response.get("results", None)

        if result_list:
            symbol = list(result_list.keys())[0]
            action = result_list.get(symbol, None)
            price = action.get("price", None)
            currency = action.get("currency", None)
            return (price, currency)

        return None, None

    '''
        Processa o corpo da resposta a ser enviada ao client
    '''
    def process_response(self, code, request):
        price, currency = self.extract_values(request)
        if not price:
            price = "\"undefined\"" #adiciona aspas extras para que o valor seja tratado como uma string json 
        if not currency:
            currency = "undefined"

        response = "{{\"symbol\": \"{}\", \"price\": {}, \"currency\": \"{}\" }}".format(code.upper(), price, currency)
        return response

    '''
        Executa uma ou mais chamadas à API externa.
    '''
    def handle_api_call(self, codes):
        response = "{ \"api_response\":["
        for code in codes:
            r = requests.get(API_ENDPOINT + code)
            if r.status_code == 200:
                processed_response = self.process_response(code, r)
                response += processed_response + ','
            else:
                self.handle_api_error()
        response = response[:-1] #remove a última vírgula
        response += "]}"
        return response

    '''
        Trata uma requisição do tipo GET.
        É a função "principal" do RequestHandler, é ela quem chama toda a pilha de validação, extração de parâmetros e chamadas à API externa diante de uma requisição do client.
    '''
    def do_GET(self):
        valid_request = self.is_valid()
        if valid_request:
            codes = self.parse_request_parameters()
            response = self.handle_api_call(codes)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(response.encode())
            sys.exit()
        else:
            self.handle_endpoint_error()

    '''
        Trata as requisições de prefight vindas do frontend
    '''
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()
        sys.exit()

    '''
        Sobrescreve a função original para habilitar CORS
    '''
    def end_headers (self):
        self.send_header('Access-Control-Allow-Origin', '*')
        SimpleHTTPRequestHandler.end_headers(self)

'''
    Função principal, instancia um servidor HTTP multithread com o set de parâmetros necessários
'''
if __name__ == '__main__':
    server = ThreadingHTTPServer(('0.0.0.0', 8080), RequestHandler)
    server.serve_forever()