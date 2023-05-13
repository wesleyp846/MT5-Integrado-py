import pandas as pd
import MetaTrader5 as mt
import time
from datetime import datetime
import asyncio

async def input_with_timeout(prompt, default, timeout=10):
    print(f"{prompt} (deixe em branco para usar '{default}')")
    try:
        coro = asyncio.wait_for(asyncio.get_event_loop().run_in_executor(None, input), timeout)
        user_input = await coro
        if user_input:
            return user_input
        else:
            return default
    except asyncio.TimeoutError:
        print(f"Tempo limite de {timeout} segundos atingido. Usando '{default}' por padrão.")
        return default
    
async def main():
    PAPEL = await input_with_timeout("Digite o codigo do papel\n", 'WINM23')
    print(''), print('')
    TEMPO_GRAFICO = await input_with_timeout("Digite o timeframe\n", 'mt.TIMEFRAME_M1')
    print(''), print('')
    LOTE = await input_with_timeout("Digite o tamanho do lote\n", '1')
    LOTE = float(LOTE)
    print(''), print('')
    COMENT = await input_with_timeout("Digite um comentário\n", 'winmbot')
    print(''), print('')
    HORA_INICIO = await input_with_timeout("Digite a hora de início\n", '09:10')
    print(''), print('')
    HORA_FIM = await input_with_timeout("Digite a hora de fim\n", '17:50')
    print(''), print('')
    LOSS = await input_with_timeout("Digite o valor de perda\n", '1000')
    LOSS = float(LOSS)
    print(''), print('')
    GAIM = await input_with_timeout("Digite o valor de ganho\n", '2500')
    GAIM = float(GAIM)
    print(''), print('')
    MAGICO = await input_with_timeout("Digite o numero magico\n", '1')
    MAGICO = int(MAGICO)
    print(''), print('')
    
    return PAPEL, TEMPO_GRAFICO, LOTE, COMENT, HORA_INICIO, HORA_FIM, LOSS, GAIM, MAGICO

# Executar o loop de eventos assíncronos
loop = asyncio.get_event_loop()
result = loop.run_until_complete(main())
loop.close()

PAPEL, TEMPO_GRAFICO, LOTE, COMENT, HORA_INICIO, HORA_FIM, LOSS, GAIM, MAGICO = result
print(f"PAPEL: {PAPEL}")
print(f"TEMPO_GRAFICO: {TEMPO_GRAFICO}")
print(f"LOTE: {LOTE}")
print(f"COMENT: {COMENT}")
print(f"HORA_INICIO: {HORA_INICIO}")
print(f"HORA_FIM: {HORA_FIM}")
print(f"LOSS: {LOSS}")
print(f"GAIM: {GAIM}")
print(f"MAGICO: {MAGICO}")
print('')

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

def aguardar_horario():
    agora = datetime.now().strftime('%H:%M')
    while agora < HORA_INICIO:
        print(f"Aguardando horário {HORA_INICIO}... agora são {agora}")
        agora = datetime.now().strftime('%H:%M')
        #if agora >= HORA_INICIO:
        #    break
        print(f"Aguardando horário {HORA_INICIO}... agora são {agora}")
        print('')
        time.sleep(60)
    print(f"agora são {agora}")



inicializacao()
aguardar_horario()


while True:
    agora = datetime.now().strftime('%H:%M')
    if agora > HORA_FIM:
        print(f'Fim do horario de {HORA_FIM} agora são {agora}')
        print('')
        break

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
        if (sma8 > sma21) and (sma21 > sma80): #and (sma80 > sma200):
            print("Cima")
            time.sleep(30)
            compra()
        elif (sma8 < sma21) and (sma21 < sma80): #and (sma80 < sma200):
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