"""Comparação entre configurações a partir de um CSV com as notas preenchidas."""
import csv
import statistics
from pathlib import Path

from erros import ErroAssistente

NOTA_MIN, NOTA_MAX = 0, 3


class ErroComparacao(ErroAssistente):
    """CSV ausente, incompleto ou com notas inválidas."""


def _numero(valor):
    try:
        return float(str(valor).replace(",", "."))
    except (TypeError, ValueError):
        return None


def ler_resultados(caminho):
    caminho = Path(caminho)
    try:
        with open(caminho, newline="", encoding="utf-8-sig") as arquivo:
            linhas = list(csv.DictReader(arquivo))
    except FileNotFoundError:
        raise ErroComparacao(f"Arquivo de resultados não encontrado: {caminho}")
    except (OSError, UnicodeDecodeError):
        raise ErroComparacao(f"Não foi possível ler {caminho.name}.")
    if not linhas:
        raise ErroComparacao(f"{caminho.name} não tem registros.")
    return linhas


def validar_notas(linhas):
    """Toda linha sem erro precisa de nota de 0 a 3. Devolve a lista de problemas."""
    problemas = []
    for linha in linhas:
        if linha.get("erro"):
            continue
        rotulo = f"{linha['caso_id']}/{linha['configuracao']}/rep{linha['repeticao']}"
        nota = _numero(linha.get("nota"))
        if nota is None:
            problemas.append(f"{rotulo}: nota não preenchida")
        elif not NOTA_MIN <= nota <= NOTA_MAX:
            problemas.append(f"{rotulo}: nota {linha['nota']} fora da escala {NOTA_MIN} a {NOTA_MAX}")
    return problemas


def _media(valores):
    valores = [v for v in valores if v is not None]
    return round(statistics.fmean(valores), 3) if valores else None


def _por_configuracao(linhas):
    nomes = sorted({l["configuracao"] for l in linhas})
    saida = {}
    for nome in nomes:
        grupo = [l for l in linhas if l["configuracao"] == nome]
        ok = [l for l in grupo if not l.get("erro")]
        ausentes = [l for l in ok if l["tipo"] == "ausente"]
        saida[nome] = {
            "execucoes": len(grupo),
            "erros": len(grupo) - len(ok),
            "nota_media": _media(_numero(l["nota"]) for l in ok),
            "latencia_media_s": _media(_numero(l["latencia_s"]) for l in ok),
            "tokens_medios": _media(_numero(l["tokens_total"]) for l in ok),
            "formato_valido_pct": round(100 * sum(l["formato_valido"] == "True" for l in ok)
                                        / len(ok), 1) if ok else None,
            "recusas": sum(l["recusa_detectada"] == "True" for l in ok),
            "ausentes_reconhecidos": sum(l["recusa_detectada"] == "True" for l in ausentes),
            "ausentes_total": len(ausentes),
        }
    return saida


def _status(delta):
    if delta is None:
        return "sem dados"
    return "melhorou" if delta > 0 else "piorou" if delta < 0 else "igual"


def _por_caso(linhas, base):
    casos = list(dict.fromkeys(l["caso_id"] for l in linhas))
    nomes = sorted({l["configuracao"] for l in linhas})
    saida = []
    for caso_id in casos:
        item = {"caso": caso_id, "notas": {}, "latencias": {}, "status": {}, "consistencia": {}}
        for nome in nomes:
            grupo = [l for l in linhas if l["caso_id"] == caso_id and l["configuracao"] == nome
                     and not l.get("erro")]
            notas = [_numero(l["nota"]) for l in grupo]
            item["notas"][nome] = _media(notas)
            item["latencias"][nome] = _media(_numero(l["latencia_s"]) for l in grupo)
            item["consistencia"][nome] = (None if len(notas) < 2 else len(set(notas)) == 1)
        for nome in nomes:
            if nome == base:
                continue
            a, b = item["notas"].get(base), item["notas"][nome]
            item["status"][nome] = _status(None if a is None or b is None else b - a)
        saida.append(item)
    return saida


def comparar(linhas, base):
    """Resumo por configuração e comparação caso a caso contra a linha de base."""
    nomes = {l["configuracao"] for l in linhas}
    if base not in nomes:
        raise ErroComparacao(f"Linha de base '{base}' não está no arquivo (há: {', '.join(sorted(nomes))}).")
    problemas = validar_notas(linhas)
    if problemas:
        raise ErroComparacao("Preencha as notas antes de comparar:\n  - " + "\n  - ".join(problemas))
    return {"base": base, "configuracoes": _por_configuracao(linhas),
            "casos": _por_caso(linhas, base)}


def _fmt(valor, sufixo=""):
    return "n/d" if valor is None else f"{valor}{sufixo}"


def renderizar_markdown(resultado):
    """Texto Markdown da comparação, pronto para o RELATORIO_EXECUCAO.md."""
    base, cfgs = resultado["base"], resultado["configuracoes"]
    nomes = list(cfgs)
    out = [f"## Comparação (linha de base: {base})", "",
           "### Resumo por configuração", "",
           "| Configuração | Execuções | Erros | Nota média | Latência média (s) | Tokens médios | Formato válido | Ausentes reconhecidos |",
           "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for nome in nomes:
        c = cfgs[nome]
        out.append(f"| {nome} | {c['execucoes']} | {c['erros']} | {_fmt(c['nota_media'])} | "
                   f"{_fmt(c['latencia_media_s'])} | {_fmt(c['tokens_medios'])} | "
                   f"{_fmt(c['formato_valido_pct'], '%')} | "
                   f"{c['ausentes_reconhecidos']} de {c['ausentes_total']} |")
    outras = [n for n in nomes if n != base]
    cabecalho = "| Caso | " + " | ".join(f"Nota {n}" for n in nomes) + " | " + \
        " | ".join(f"{n} vs {base}" for n in outras) + " | Latência (s) |"
    out += ["", "### Caso a caso", "", cabecalho,
            "|" + " --- |" * (1 + len(nomes) + len(outras) + 1)]
    for item in resultado["casos"]:
        notas = " | ".join(_fmt(item["notas"].get(n)) for n in nomes)
        status = " | ".join(item["status"].get(n, "") for n in outras)
        lat = " / ".join(f"{n}: {_fmt(item['latencias'].get(n))}" for n in nomes)
        out.append(f"| {item['caso']} | {notas} | {status} | {lat} |")
    cont = {n: {"melhorou": 0, "igual": 0, "piorou": 0} for n in outras}
    for item in resultado["casos"]:
        for n in outras:
            if item["status"].get(n) in cont[n]:
                cont[n][item["status"][n]] += 1
    out += ["", "### Balanço contra a linha de base", ""]
    for n in outras:
        c = cont[n]
        out.append(f"- {n}: {c['melhorou']} caso(s) melhoraram, {c['igual']} ficaram iguais e "
                   f"{c['piorou']} pioraram.")
    return "\n".join(out) + "\n"
