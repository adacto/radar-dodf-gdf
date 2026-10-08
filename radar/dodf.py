"""Cliente da API do DODF.

Contrato medido contra o servidor em 08/10/2026, não inferido de documentação.
As rotas do DODFMiner (/index/jornal-json, /listar?dir=) estão MORTAS (404).
"""
import json
import time
import urllib.parse
import urllib.request

BASE = "https://dodf.df.gov.br"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) radar-dodf-gdf"
PAUSA = 0.35


def _post(caminho, campos, tentativas=4):
    """POST com recuo exponencial. Devolve o JSON ou levanta."""
    dados = urllib.parse.urlencode(campos, doseq=True).encode()
    req = urllib.request.Request(
        BASE + caminho,
        data=dados,
        headers={
            "User-Agent": UA,
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    erro = None
    for n in range(tentativas):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # rede, 5xx, JSON malformado
            erro = e
            time.sleep(2 ** n)
    raise RuntimeError("falhou %s: %s" % (caminho, erro))


def edicoes_do_mes():
    """Calendário do mês corrente: {'20261008': ['integra', 'extra'], ...}.

    O endpoint ignora parâmetros de mês/ano — só devolve o mês atual.
    """
    return _post("/dodf/jornal/indicador", {}).get("data", {})


def diario(ts, pagina=1):
    """Uma página do diário do dia. `ts` é unix timestamp da meia-noite local."""
    return _post(
        "/dodf/jornal/diario",
        {"data": ts, "pagina": pagina, "tpJornal": "", "letra": ""},
    )


def diario_completo(ts):
    """Varre todas as páginas do dia.

    Devolve (materias, arvore_de_orgaos, data_confirmada_pelo_servidor).
    """
    primeira = diario(ts, 1)
    total_pag = primeira.get("totalPaginas", 0) or 0
    confirmada = (primeira.get("data") or [None])[0]
    materias = list(primeira.get("lstMaterias") or [])
    arvore = (primeira.get("lstDemandantesMateria") or {}).get("demandantes") or {}
    for p in range(2, total_pag + 1):
        time.sleep(PAUSA)
        pag = diario(ts, p)
        materias.extend(pag.get("lstMaterias") or [])
        arvore.update((pag.get("lstDemandantesMateria") or {}).get("demandantes") or {})
    return materias, arvore, confirmada


def inteiro_teor(co_materia, slug=""):
    """HTML do ato completo.

    O parâmetro é `co_data`, NÃO `co_materia` — errar devolve 204 vazio.
    Necessário para créditos suplementares: o preâmbulo do decreto consome
    os ~500 caracteres do trecho da listagem antes de chegar ao valor.
    """
    url = BASE + "/dodf/materia/visualizar?" + urllib.parse.urlencode(
        {"co_data": co_materia, "p": slug}
    )
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for n in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8", "replace")
        except Exception:
            time.sleep(2 ** n)
    return ""


def link(co_materia, slug=""):
    """URL pública do ato, para o boletim."""
    return BASE + "/dodf/materia/visualizar?" + urllib.parse.urlencode(
        {"co_data": co_materia, "p": slug}
    )
