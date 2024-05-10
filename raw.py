#############################################################################
# PROJETO DE REDES
# GRUPO: Ana Luisa Miranda Pessoa, Beatriz Saori Kyohara, Helio Lima Correia II
# PROFESSOR: Fernando Menezes Matos
# socket RAW com protocolo IPPROTO_UDP
#############################################################################


import types
import random
import socket

consts = types.SimpleNamespace()
consts.DATA = 1
consts.MOTIVATIONAL_MESSAGE = 2
consts.SERVER_RESPONSE_COUNT = 3

IP_DESTINO = '15.228.191.109'
PORTA_DESTINO = 0xC350

def splitNumberInto2Bytes(number):
    '''Divide um número em dois bytes.'''
    number = number.to_bytes(2, byteorder='big')
    return number

def transformIPStringToBytes(ip):
    '''Transforma uma string de IP em bytes.'''
    string_list = ip.split('.')
    int_list = [int(i) for i in string_list]
    return bytes(int_list)

def displayOptions():
    '''Exibe as opções de requisição do usuário.'''
    print("Opções de solicitação para você usuário:")
    print("1 ==> Exibe a Data e hora atual")
    print("2 ==> Exibe uma mensagem motivacional para o final do semestre")
    print("3 ==> Exibe a quantidade de respostas emitidas pelo servidor até o momento")
    print("4 ==> Sair")

def createRequest(type, identifier):
    '''Cria uma mensagem de requisição com base no tipo e no identificador.'''
    byte1 = 0b00000000
    bytes_identifier = splitNumberInto2Bytes(identifier)
    match type:
        case consts.DATA:
            byte1 = byte1 | 0b0000
        case consts.MOTIVATIONAL_MESSAGE:
             byte1 = byte1 | 0b0001
        case consts.SERVER_RESPONSE_COUNT:
            byte1 = byte1 | 0b0010
        case _:
            byte1 = byte1 | 0b0011

    message = bytes([byte1, bytes_identifier[0], bytes_identifier[1]])
    return message

def generateRandomIdentifier():
    '''Gera um identificador aleatório entre 1 e 65535.'''
    return random.randint(1, 65535)

def add16BitWords(word1, word2):
    '''Adiciona duas palavras de 16 bits e caso ela exceda corrije com o Carry.'''
    result = word1 + word2
    while result.bit_length() > 16:
        carry = result >> 16
        result &= 0xFFFF
        result += carry
    return result

def calculateChecksum(byte_list):
    '''Calcula o checksum de uma lista de bytes.'''
    list_size = len(byte_list)
    if list_size % 2 != 0:
        byte_list += bytes([0])
    list_size = len(byte_list)
    index = 0x0000
    result = 0x0000
    for _ in range(int(list_size / 4)):
        result = add16BitWords(result, add16BitWords(byte_list[index] << 8 | byte_list[index + 1],
                                                     byte_list[index + 2] << 8 | byte_list[index + 3]))
        index += 4
    return ~result & 0xFFFF

def bytesToString(byte_list):
    '''Converte uma lista de bytes em uma string.'''
    return ''.join(chr(i) for i in byte_list)

def bytesToInt(byte_list):
    '''Converte uma lista de bytes em um número inteiro.'''
    return int.from_bytes(bytes(byte_list), byteorder = 'big')

def decodeResponse(data):
    '''Decodifica os dados da resposta.'''
    type = data[0]
    response_size = data[3]
    byte_list = []
    if type in [0x10, 0x11, 0x12]:
        for i in range(response_size):
            byte_list.append(data[4+i])
        if type in [0x10, 0x11]:
            return bytesToString(byte_list)
        elif type == 0x12:
            return bytesToInt(byte_list)


def assembleUDPHeader(source_port, destination_port, udp_packet_size, udp_checksum):
    '''Monta o cabeçalho UDP.'''
    ''' Convertendo números em bytes '''
    source_port = splitNumberInto2Bytes(source_port)
    destination_port = splitNumberInto2Bytes(destination_port)
    udp_packet_size = splitNumberInto2Bytes(udp_packet_size)
    udp_checksum = splitNumberInto2Bytes(udp_checksum)

    ''' Monta o cabeçalho UDP '''
    udp_header = bytes([source_port[0], source_port[1], destination_port[0], destination_port[1], udp_packet_size[0], udp_packet_size[1], udp_checksum[0], udp_checksum[1]])
    return udp_header

def assemblePseudoHeader(source_ip, destination_ip, udp_packet_size):
    '''Monta o pseudo cabeçalho solicitado.'''
    protocol = socket.IPPROTO_UDP.to_bytes(1, byteorder = 'big')
    source_ip = transformIPStringToBytes(source_ip)
    destination_ip = transformIPStringToBytes(destination_ip)
    zero = 0b00000000
    udp_packet_size = splitNumberInto2Bytes(udp_packet_size)
    pseudo_header = source_ip + destination_ip + bytes([zero, protocol[0], udp_packet_size[0], udp_packet_size[1]])
    return pseudo_header

def extractPayload(data):
    '''Extrai a carga útil dos dados recebidos.'''
    '''Ignorar os primeiros 28 bytes para obter a carga útil'''
    payload = data[28:]
    return payload

def findSourcePort():
    '''Encontra a porta de origem.'''
    sock = socket.socket()
    sock.bind(('', 0))
    return sock.getsockname()[1]

def findSourceIP():
    '''Encontra o IP de origem.'''
    hostname = socket.gethostname()
    return socket.gethostbyname(hostname)


def main():
    print("RAW CLIENT VIP")
    displayOptions()
    while True:
        tipo = input("Insira uma solicitação válida: ")
        if (tipo == '4'):
            print("Encerrando o programa como solicitado...")
            break

        data = createRequest(int(tipo), generateRandomIdentifier())

        porta_origem = 0xE713
        ''' Monta o socket raw usando o socket de internet e o protocolo solicitado'''
        socket_raw = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_UDP)
        tamanho_pacote_udp = 8 + len(data)    
        udp_checksum = 0x0000                          
        pacote_udp = assembleUDPHeader(porta_origem, PORTA_DESTINO, tamanho_pacote_udp, udp_checksum)
        segmento = pacote_udp + data

       
        ip_origem = findSourceIP()
        pseudo_cabecalho = assemblePseudoHeader(ip_origem, IP_DESTINO, tamanho_pacote_udp)
        udp_checksum = calculateChecksum(pseudo_cabecalho + segmento)

        pacote_udp = assembleUDPHeader(porta_origem, PORTA_DESTINO, tamanho_pacote_udp, udp_checksum)

        endereco_destino = (IP_DESTINO, PORTA_DESTINO)       
        socket_raw.sendto(segmento, endereco_destino)

        dados, _ = socket_raw.recvfrom(1040)    
        payload = extractPayload(dados)
        resposta = decodeResponse(payload)  
        print(resposta)


if __name__ == "__main__":
    main()
