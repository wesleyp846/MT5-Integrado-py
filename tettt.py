import pandas as pd
import MetaTrader5 as mt
import time
from datetime import datetime
import asyncio
import csv
from tkinter import *

LOGSAIDA = "prints.csv"

def salvar_print_csv(mensagem):
    with open(LOGSAIDA, "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), mensagem])

async def input_with_timeout(prompt, default, timeout=10):
    print(f"{prompt} (deixe em branco para usar '{default}')")
    salvar_print_csv(f"{prompt} (deixe em branco para usar '{default}')")
    try:
        coro = asyncio.wait_for(asyncio.get_event_loop().run_in_executor(None, input), timeout)
        user_input = await coro
        if user_input:
            return user_input
        else:
            return default
    except asyncio.TimeoutError:
        print(f"Tempo limite de {timeout} segundos atingido. Usando '{default}' por padrão.")
        salvar_print_csv(f"Tempo limite de {timeout} segundos atingido. Usando '{default}' por padrão.")
        return default

async def main():
    PAPEL = await input_with_timeout('Digite o código do papel\n', 'WINM23')
    print(''), print('')
    TEMPO_GRAFICO = await input_with_timeout('Digite o timeframe\n', 'mt.TIMEFRAME_M1')
    print(''), print('')
    LOTE = await input_with_timeout('Digite o tamanho do lote\n', '1')
    LOTE = float(LOTE)
    print(''), print('')
    COMENT = await input_with_timeout('Digite um comentário\n', 'versao3b')
    print(''), print('')
    HORA_INICIO = await input_with_timeout('Digite a hora de início\n', '09:10')
    print(''), print('')
    HORA_FIM = await input_with_timeout('Digite a hora de fim\n', '17:50')
    print(''), print('')
    LOSS = await input_with_timeout('Digite o valor de perda\n', '1000')
    LOSS = float(LOSS)
    print(''), print('')
    GAIM = await input_with_timeout('Digite o valor de ganho\n', '2500')
    GAIM = float(GAIM)
    print(''), print('')
    MAGICO = await input_with_timeout('Digite o número mágico\n', '1')
    MAGICO = int(MAGICO)
    print(''), print('')
    
    return PAPEL, TEMPO_GRAFICO, LOTE, COMENT, HORA_INICIO, HORA_FIM, LOSS, GAIM, MAGICO

# Executar o loop de eventos assíncronos
loop = asyncio.get_event_loop()
result = loop.run_until_complete(main())
loop.close()

PAPEL, TEMPO_GRAFICO, LOTE, COMENT, HORA_INICIO, HORA_FIM, LOSS, GAIM, MAGICO = result

def obter_informacoes():
    papel = PAPEL
    timeframe = TEMPO_GRAFICO
    lote = LOTE
    coment = COMENT
    hora_inicio = HORA_INICIO
    hora_fim = HORA_FIM
    perda = LOSS
    ganho = GAIM
    magico = MAGICO

    # Exibir as informações no terminal
    print(f'PAPEL: {papel}')
    print(f'TEMPO_GRAFICO: {timeframe}')
    print(f'LOTE: {lote}')
    print(f'COMENT: {coment}')
    print(f'HORA_INICIO: {hora_inicio}')
    print(f'HORA_FIM: {hora_fim}')
    print(f'LOSS: {perda}')
    print(f'GAIM: {ganho}')
    print(f'MAGICO: {magico}')
    print('')

    # Salvar as informações no arquivo CSV
    salvar_print_csv(result)

def inicializacao():
    try:
        mt.initialize()
        symbol_info = mt.symbol_info(PAPEL)
        if symbol_info is None:
            print(PAPEL, 'não encontrado')
            salvar_print_csv(PAPEL, 'não encontrado')
            quit()
        elif not symbol_info.visible:
            print(PAPEL, 'não está visível na Market Watchlist, adicionando agora...')
            salvar_print_csv(PAPEL, 'não está visível na Market Watchlist, adicionando agora...')
            if not mt.symbol_select(PAPEL, True):
                print(f'Não foi possível adicionar {PAPEL} à lista de Market Watchlist')
                salvar_print_csv(f'Não foi possível adicionar {PAPEL} à lista de Market Watchlist')
                quit()
        print('Inicialização concluída com sucesso!')
        salvar_print_csv('Inicialização concluída com sucesso!')
    except Exception as e:
        print('Erro na inicialização:', e)
        salvar_print_csv('Erro na inicialização:', e)
        quit()

def get_ohlc_with_ema(PAPEL, TEMPO_GRAFICO, n=202):
    ativo = mt.copy_rates_from_pos(PAPEL, TEMPO_GRAFICO, 0, n)
    ativo = pd.DataFrame(ativo)
    ativo['time'] = pd.to_datetime(ativo['time'], unit='s')
    ativo.set_index('time', inplace=True)
    ativo['sma8'] = ativo['close'].rolling(window=8).mean()
    ativo['sma21'] = ativo['close'].rolling(window=21).mean()
    ativo['sma80'] = ativo['close'].rolling(window=30).mean()
    ativo['sma200'] = ativo['close'].rolling(window=200).mean()
    return ativo

def venda():
    lot = LOTE
    symbol = PAPEL
    point = mt.symbol_info(symbol).point
    price = mt.symbol_info_tick(symbol).bid
    desviation = 1
    tp = price - GAIM * point
    sl = price + LOSS * point
    request = {
        'action': mt.TRADE_ACTION_DEAL,
        'symbol': symbol,
        'volume': lot,
        'type': mt.ORDER_TYPE_SELL,
        'price': price,
        'tp': tp,
        'sl': sl,
        'magic': MAGICO,
        'desviation': desviation,
        'comment': COMENT,
        'type_time': mt.ORDER_TIME_GTC,
        'type_filling': mt.ORDER_FILLING_RETURN,
    }
    return mt.order_send(request), print(f'>>>Vendendo {lot} de {symbol} preço {price} com tp {tp} e sl {sl}'), print(""), salvar_print_csv(f'>>>Vendendo {lot} de {symbol} preço {price} com tp {tp} e sl {sl}')

def compra():
    lot = LOTE
    symbol = PAPEL
    point = mt.symbol_info(symbol).point
    price = mt.symbol_info_tick(symbol).ask
    desviation = 1
    tp = price + GAIM * point
    sl = price - LOSS * point
    request = {
        'action': mt.TRADE_ACTION_DEAL,
        'symbol': symbol,
        'volume': lot,
        'type': mt.ORDER_TYPE_BUY,
        'price': price,
        'tp': tp,
        'sl': sl,
        'magic': MAGICO,
        'desviation': desviation,
        'comment': COMENT,
        'type_time': mt.ORDER_TIME_GTC,
        'type_filling': mt.ORDER_FILLING_RETURN,
    }
    return mt.order_send(request), print(f'>>>Comprando {lot} de {symbol} preço {price} com tp {tp} e sl {sl}'), print(""), salvar_print_csv(f'>>>Comprando {lot} de {symbol} preço {price} com tp {tp} e sl {sl}')

def fechar_dia():
    posicoes = mt.positions_get(symbol=PAPEL)
    for posicao in posicoes:
        if posicao.type == 0:
            posicao = 'comprado'
        elif posicao.type == 1:
            posicao = 'vendido'
    if len(posicoes) > 0:
        if posicao == 'comprado':
            venda()
        elif posicao == 'vendido':
            compra()
    mt.shutdown()

def aguardar_horario():
    agora = datetime.now().strftime('%H:%M')
    while agora < HORA_INICIO:
        agora = datetime.now().strftime('%H:%M')
        print(f'Aguardando horário {HORA_INICIO}... agora são {agora}')
        salvar_print_csv(f'Aguardando horário {HORA_INICIO}... agora são {agora}')
        print('')
        time.sleep(60)
    print(f'Agora são {agora}')
    salvar_print_csv(f'Agora são {agora}')


# Interface gráfica com o Tkinter
root = Tk()
root.title("Terminal Output")
root.geometry("800x600")

# Componente Text para exibir a saída do terminal
text_output = Text(root, height=30, width=100)
text_output.pack()

# Redirecionar a saída padrão para o componente Text
sys.stdout = text_output

# Função para atualizar a saída no componente Text
def update_output():
    text_output.update_idletasks()

# Função para exibir as mensagens no componente Text
def print_to_output(message):
    print(message)
    update_output()

# Executar o loop de eventos assíncronos
loop = asyncio.get_event_loop()
result = loop.run_until_complete(main())
loop.close()

PAPEL, TEMPO_GRAFICO, LOTE, COMENT, HORA_INICIO, HORA_FIM, LOSS, GAIM, MAGICO = result

print_to_output(f'PAPEL: {PAPEL}')
print_to_output(f'TEMPO_GRAFICO: {TEMPO_GRAFICO}')
print_to_output(f'LOTE: {LOTE}')
print_to_output(f'COMENT: {COMENT}')
print_to_output(f'HORA_INICIO: {HORA_INICIO}')
print_to_output(f'HORA_FIM: {HORA_FIM}')
print_to_output(f'LOSS: {LOSS}')
print_to_output(f'GAIM: {GAIM}')
print_to_output(f'MAGICO: {MAGICO}')
print_to_output('')
salvar_print_csv('PAPEL: ' + PAPEL)
salvar_print_csv('TEMPO_GRAFICO: ' + TEMPO_GRAFICO)
salvar_print_csv('LOTE: ' + str(LOTE))
salvar_print_csv('COMENT: ' + COMENT)
salvar_print_csv('HORA_INICIO: ' + HORA_INICIO)
salvar_print_csv('HORA_FIM: ' + HORA_FIM)
salvar_print_csv('LOSS: ' + str(LOSS))
salvar_print_csv('GAIM: ' + str(GAIM))
salvar_print_csv('MAGICO: ' + str(MAGICO))
print_to_output('')

inicializacao()

while True:
    aguardar_horario()
    ohlc = get_ohlc_with_ema(PAPEL, TEMPO_GRAFICO)
    fechar_dia()
    if ohlc.iloc[-2]['close'] < ohlc.iloc[-2]['sma80'] and ohlc.iloc[-1]['close'] > ohlc.iloc[-1]['sma80']:
        compra()
    elif ohlc.iloc[-2]['close'] > ohlc.iloc[-2]['sma80'] and ohlc.iloc[-1]['close'] < ohlc.iloc[-1]['sma80']:
        venda()
    time.sleep(60)

root.mainloop()
