#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
External check Zabbix para ar-condicionado de gabinete AC110-2 / controlador ZL-U09D2-SL.

Exemplo manual:
  /usr/lib/zabbix/externalscripts/ar_condicionado_modbus.py --ip 192.168.20.231 --port 502 --unit 1

Exemplo de key no Zabbix:
  ar_condicionado_modbus.py["--ip","{$ARCOND.IP}","--port","{$ARCOND.PORT}","--unit","{$ARCOND.UNIT}"]
"""

import argparse
import inspect
import json
import sys

try:
    from pymodbus.client import ModbusTcpClient
except Exception as e:
    print(json.dumps({
        "status": "error",
        "error": "pymodbus_import_error",
        "message": str(e)
    }, ensure_ascii=False))
    sys.exit(1)


DEFAULT_IP = "192.168.20.231"
DEFAULT_PORT = 502
DEFAULT_UNIT_ID = 1
DEFAULT_TIMEOUT = 3

HOLDING_START = 0
HOLDING_COUNT = 36

COIL_START = 0
COIL_COUNT = 32


def signed_16(value: int) -> int:
    return value - 65536 if value >= 32768 else value


def scale_x10(value: int) -> float:
    return round(signed_16(value) / 10.0, 1)


def call_modbus_method(method, address, count, unit_id):
    params = inspect.signature(method).parameters

    if "device_id" in params:
        return method(address=address, count=count, device_id=unit_id)
    if "slave" in params:
        return method(address=address, count=count, slave=unit_id)
    if "unit" in params:
        return method(address=address, count=count, unit=unit_id)

    return method(address, count)


def read_holding(client, address, count, unit_id):
    return call_modbus_method(client.read_holding_registers, address, count, unit_id)


def read_coils(client, address, count, unit_id):
    return call_modbus_method(client.read_coils, address, count, unit_id)


def bit_value(bits, coil_number, default=0):
    index = coil_number - 1
    if index < 0 or index >= len(bits):
        return default
    return 1 if bool(bits[index]) else 0


def mode_text(value):
    return {
        0: "normal_control",
        1: "force_on",
        2: "force_off",
    }.get(value, "unknown")


def enable_text(value):
    return {
        0: "disabled",
        1: "enabled",
    }.get(value, "unknown")


def power_text(value):
    return {
        0x0000: "off",
        0xFF00: "on",
    }.get(value, "unknown")


def decode_holding_registers(reg):
    data = {
        "temp_interna": scale_x10(reg[0]),
        "temp_externa": scale_x10(reg[1]),
        "umidade": scale_x10(reg[5]),

        "refrigeracao_liga_temp": scale_x10(reg[8]),
        "refrigeracao_desliga_temp": scale_x10(reg[9]),
        "aquecimento_liga_temp": scale_x10(reg[10]),
        "aquecimento_desliga_temp": scale_x10(reg[11]),
        "heat_pipe_liga_temp": scale_x10(reg[12]),
        "heat_pipe_desliga_temp": scale_x10(reg[13]),

        "alarme_alta_temp_set": scale_x10(reg[14]),
        "alarme_baixa_temp_set": scale_x10(reg[15]),

        "desumidificacao_liga_umidade": scale_x10(reg[16]),
        "desumidificacao_desliga_umidade": scale_x10(reg[17]),

        "calibracao_sensor_temp_1": scale_x10(reg[18]),
        "calibracao_sensor_temp_2": scale_x10(reg[19]),

        "pressao_alarme_config": reg[20],
        "sensor_temp_1_habilitado": reg[21],
        "sensor_temp_1_habilitado_texto": enable_text(reg[21]),
        "sensor_temp_2_habilitado": reg[22],
        "sensor_temp_2_habilitado_texto": enable_text(reg[22]),
        "sensor_umidade_habilitado": reg[23],
        "sensor_umidade_habilitado_texto": enable_text(reg[23]),

        "modo_compressor": reg[24],
        "modo_compressor_texto": mode_text(reg[24]),
        "modo_aquecimento_eletrico": reg[25],
        "modo_aquecimento_eletrico_texto": mode_text(reg[25]),
        "modo_ventilador_interno": reg[26],
        "modo_ventilador_interno_texto": mode_text(reg[26]),
        "modo_ventilador_externo": reg[27],
        "modo_ventilador_externo_texto": mode_text(reg[27]),

        "falha_sensor_temp_1_config": reg[28],
        "falha_sensor_temp_2_config": reg[29],
        "falha_sensor_umidade_config": reg[30],
        "falha_alarme_alta_temp_config": reg[31],
        "falha_alarme_baixa_temp_config": reg[32],
        "falha_alarme_pressao_config": reg[33],
        "falha_alarme_congelamento_config": reg[34],

        "sistema_power_raw": reg[35],
        "sistema_power_texto": power_text(reg[35]),

        # Compatibilidade com templates/testes anteriores
        "limite_superior_provavel": scale_x10(reg[8]),
        "setpoint_provavel": scale_x10(reg[9]),

        "raw_registers": reg,
    }

    for i, value in enumerate(reg):
        data[f"reg_{i}"] = value

    return data


def decode_coils(bits):
    data = {
        "coils_read_ok": 1,

        "alarme_falha_sensor_rt1": bit_value(bits, 1),
        "alarme_falha_sensor_rt2": bit_value(bits, 2),
        "alarme_falha_sensor_umidade": bit_value(bits, 6),
        "alarme_erro_eeprom": bit_value(bits, 7),
        "maquina_ligada": bit_value(bits, 8),
        "alarme_alta_temp": bit_value(bits, 9),
        "alarme_baixa_temp": bit_value(bits, 10),
        "alarme_pressao_compressor": bit_value(bits, 13),
        "alarme_congelamento": bit_value(bits, 14),

        "compressor_ligado": bit_value(bits, 17),
        "aquecimento_eletrico_ligado": bit_value(bits, 18),
        "ventilador_interno_ligado": bit_value(bits, 19),
        "ventilador_externo_ligado": bit_value(bits, 20),
        "hidrogenio_ligado": bit_value(bits, 21),

        "raw_coils": [1 if b else 0 for b in bits[:COIL_COUNT]],
    }

    alarm_keys = [
        "alarme_falha_sensor_rt1",
        "alarme_falha_sensor_rt2",
        "alarme_falha_sensor_umidade",
        "alarme_erro_eeprom",
        "alarme_alta_temp",
        "alarme_baixa_temp",
        "alarme_pressao_compressor",
        "alarme_congelamento",
    ]
    data["alarme_ativo"] = 1 if any(data[k] for k in alarm_keys) else 0
    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default=DEFAULT_IP)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--unit", type=int, default=DEFAULT_UNIT_ID)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument("--no-coils", action="store_true")
    args = parser.parse_args()

    client = ModbusTcpClient(host=args.ip, port=args.port, timeout=args.timeout)

    try:
        if not client.connect():
            print(json.dumps({
                "status": "error",
                "error": "falha_conexao_tcp",
                "ip": args.ip,
                "port": args.port,
                "unit_id": args.unit,
            }, ensure_ascii=False, separators=(",", ":")))
            sys.exit(1)

        rr = read_holding(client, HOLDING_START, HOLDING_COUNT, args.unit)

        if rr is None:
            print(json.dumps({"status": "error", "error": "sem_resposta_holding"}, ensure_ascii=False, separators=(",", ":")))
            sys.exit(1)

        if hasattr(rr, "isError") and rr.isError():
            print(json.dumps({
                "status": "error",
                "error": "erro_modbus_holding",
                "response": str(rr),
            }, ensure_ascii=False, separators=(",", ":")))
            sys.exit(1)

        registers = getattr(rr, "registers", [])
        if len(registers) < HOLDING_COUNT:
            print(json.dumps({
                "status": "error",
                "error": "holding_incompleto",
                "received": len(registers),
                "expected": HOLDING_COUNT,
            }, ensure_ascii=False, separators=(",", ":")))
            sys.exit(1)

        data = {
            "status": "ok",
            "ip": args.ip,
            "port": args.port,
            "unit_id": args.unit,
        }
        data.update(decode_holding_registers(registers[:HOLDING_COUNT]))

        if args.no_coils:
            data["coils_read_ok"] = 0
            data["coil_error"] = "disabled_by_argument"
        else:
            cr = read_coils(client, COIL_START, COIL_COUNT, args.unit)
            if cr is None or (hasattr(cr, "isError") and cr.isError()) or not hasattr(cr, "bits"):
                data["coils_read_ok"] = 0
                data["coil_error"] = str(cr)
            else:
                data.update(decode_coils(cr.bits[:COIL_COUNT]))

        print(json.dumps(data, ensure_ascii=False, separators=(",", ":")))

    except Exception as e:
        print(json.dumps({
            "status": "error",
            "error": "exception",
            "message": str(e),
            "ip": args.ip,
            "port": args.port,
            "unit_id": args.unit,
        }, ensure_ascii=False, separators=(",", ":")))
        sys.exit(1)

    finally:
        client.close()


if __name__ == "__main__":
    main()
