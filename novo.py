import pandas as pd
import MetaTrader5 as mt
import time
from datetime import datetime
    
# Entrada de dados
PAPEL = input("Digite o nome do papel: (exemplo: WINM23)\n") or 'WINM23'
TEMPO_GRAFICO = input("Digite o timeframe (exemplo: mt.TIMEFRAME_M1):\n") or mt.TIMEFRAME_M1
LOTE = float(input("Digite o tamanho do lote: (exemplo: 1)\n") or 1)
COMENT = input("Digite um comentário:\n") or 'winmbot'
HORA_INICIO = input("Digite a hora de início (formato '09:10'):\n") or '09:10'
HORA_FIM = input("Digite a hora de fim (formato '17:50'):\n") or '17:50'
LOSS = float(input("Digite o valor de perda (exemplo: 1000):\n") or 1000)
GAIM = float(input("Digite o valor de ganho (exemplo: 2500):\n") or 2500)
MAGICO = int(input("Digite um valor (ou deixe em branco para usar o valor padrão 1):\n") or 1)


def inicializacao():
    try:
        mt.initialize()
        symbol_info = mt.symbol_info(PAPEL)
        if symbol_info is None:
            print(PAPEL, 'não encontrado')
            quit()
        elif not symbol_info.visible:
            print(PAPEL, 'não está visível na Market Watchlist, adicionando agora...')
            if not mt.symbol_select(PAPEL, True):
                print(f'Não foi possível adicionar {PAPEL} à lista de Market Watchlist')
                quit()
        print('Inicialização concluída com sucesso!')
    except Exception as e:
        print('Erro na inicialização:', e)
        quit()

def get_ohlc_with_ema(PAPEL, TEMPO_GRAFICO, n=202):
    ativo = mt.copy_rates_from_pos(PAPEL, TEMPO_GRAFICO, 0, n)
    ativo = pd.DataFrame(ativo)
    ativo['time'] = pd.to_datetime(ativo['time'], unit='s')
    ativo.set_index('time', inplace=True)
    ativo['sma8'] = ativo['close'].rolling(window=8).mean()
    ativo['sma21'] = ativo['close'].rolling(window=21).mean()
    ativo['sma80'] = ativo['close'].rolling(window=80).mean()
    ativo['sma200'] = ativo['close'].rolling(window=200).mean()
    return ativo

def venda():
    lot=LOTE
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
    return mt.order_send(request), print(f'>>>Vendendo {lot} de {symbol} preço {price} com tp {tp} e sl {sl}'), print("")

def compra():
    lot=LOTE
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
    return mt.order_send(request), print(f'>>>Comprando {lot} de {symbol} preço {price} com tp {tp} e sl {sl}'), print("")

def timer():
    now = datetime.now().strftime('%H:%M')
    return now

def fechar_dia():
    posicoes = mt.positions_get(symbol=PAPEL)
    for posicao in posicoes:
        if posicao.type == 0:
            posicao = "comprado"
        elif posicao.type == 1:
            posicao = "vendido"
    if len(posicoes) > 0:
        if posicao == "comprado":
            venda()
        elif posicao == "vendido":
            compra()
    mt.shutdown()

inicializacao()
timer()

while HORA_INICIO <= timer() <= HORA_FIM:
    timer()
    resultado = get_ohlc_with_ema(PAPEL, mt.TIMEFRAME_M1)
    sma8 = resultado['sma8'].iloc[-1]
    sma21 = resultado['sma21'].iloc[-1]
    sma80 = resultado['sma80'].iloc[-1]
    sma200 = resultado['sma200'].iloc[-1]

    posicoes = mt.positions_get(symbol=PAPEL)

    for posicao in posicoes:
        if posicao.type == 0:
            posicao="comprado"
        elif posicao.type == 1:
            posicao="vendido"

    if len(posicoes) == 0:
        if (sma8 > sma21) and (sma21 > sma80) and (sma80 > sma200):
            print("Cima")
            time.sleep(30)
            compra()
        elif (sma8 < sma21) and (sma21 < sma80) and (sma80 < sma200):
            print("Baixo")
            time.sleep(30)
            venda()
    elif len(posicoes) > 0:
        if posicao == "comprado":
            if (sma8 < sma21):
                print('sair da compra')
                venda()
        elif posicao == "vendido":
            if (sma8 > sma21):
                print('sair da venda')
                compra()
    time.sleep(3)

fechar_dia()