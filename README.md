
# Zabbix Template - AC Cabinet AC110-2 / ZL-U09D2-SL

Template Zabbix para monitoramento do ar-condicionado de gabinete **AC Cabinet AC110-2**, equipado com controlador **ZL-U09D2-SL**.

A coleta é realizada por um script Python executado pelo **Zabbix Proxy** ou **Zabbix Server** como **External Check**. O script consulta o equipamento por meio de um gateway **Modbus TCP para RS485** e retorna um JSON único, utilizado pelo template como item mestre.

A partir desse JSON, o template cria itens dependentes para monitorar temperatura, status operacional, alarmes, registradores e coils do controlador.

## Visão geral

O template utiliza o modelo de **item mestre + itens dependentes**.

O item mestre executa o script externo `ar_condicionado_modbus`, armazena o JSON completo da coleta e os itens dependentes extraem os campos necessários via JSONPath.

## Recursos monitorados

* Temperatura interna e externa
* Umidade
* Setpoints de refrigeração e alarmes
* Estado da máquina
* Estado do compressor
* Estado dos ventiladores interno e externo
* Aquecimento elétrico
* Alarmes do controlador
* Coils Modbus
* Holding registers
* Dados brutos para diagnóstico

## Funcionamento da coleta

O item mestre utiliza a seguinte chave no Zabbix:

```text
ar_condicionado_modbus["--ip","{$ARCOND.IP}","--port","{$ARCOND.PORT}","--unit","{$ARCOND.UNIT}","--timeout","{$ARCOND.TIMEOUT}"]
```

As principais macros utilizadas são:

| Macro                 | Descrição                   |
| --------------------- | --------------------------- |
| `{$ARCOND.IP}`        | IP do gateway Modbus TCP    |
| `{$ARCOND.PORT}`      | Porta Modbus TCP            |
| `{$ARCOND.UNIT}`      | Unit ID / Slave ID Modbus   |
| `{$ARCOND.TIMEOUT}`   | Timeout da coleta           |
| `{$ARCOND.NODATA}`    | Tempo sem dados para alerta |
| `{$ARCOND.TEMP.WARN}` | Temperatura de aviso        |
| `{$ARCOND.TEMP.HIGH}` | Temperatura alta            |

## Alertas

O template possui triggers para:

* Falha ou ausência de coleta
* Erro na leitura dos coils
* Temperatura interna em aviso
* Temperatura interna alta
* Temperatura acima do setpoint de alarme
* Compressor não acionando acima do ponto de refrigeração
* Refrigeração possivelmente ineficiente
* Alarmes ativos no controlador
* Falhas de sensores
* Falha de pressão do compressor
* Alarme de congelamento
* Erro de EEPROM
* Máquina ou sistema desligado

## Gráficos

O template inclui gráficos para acompanhamento de:

* Temperaturas e setpoints
* Estados operacionais
* Alarmes do controlador

## Observações

Este projeto não cobre instalação do Zabbix, configuração de proxy, permissões de sistema ou instalação de bibliotecas Python.

O foco é disponibilizar o template, o script de coleta e a estrutura necessária para monitoramento operacional do controlador **ZL-U09D2-SL** via Zabbix.
