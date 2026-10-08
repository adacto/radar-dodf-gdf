"""A peneira: decide o que, num diário de ~386 atos, pede atenção.

Regra central, medida sobre 10 dias (3.864 atos): o gatilho vale quando casa
no TÍTULO ou no TIPO do ato, não no corpo. Buscar no corpo inflava os números
entre 22% e 100% — todo contrato cita "dotação orçamentária" e toda rescisão
aparece como cláusula em aditivos que não são rescisões.

Exceção: crédito suplementar. O título de um decreto é só o número, e o
preâmbulo consome o trecho visível da listagem. Esse sinal exige o inteiro
teor — 14 dos 17 do período não apareciam no resumo.
"""
import re
import unicodedata


def normalizar(s):
    s = unicodedata.normalize("NFD", s or "")
    return "".join(c for c in s if unicodedata.category(c) != "Mn").upper()


# (chave, rótulo, grupo, regex no título/tipo)
GATILHOS = [
    ("divida", "Reconhecimento de dívida", "risco",
     r"RECONHECIMENTO DE DIVIDA"),
    ("penalidade", "Penalidade a fornecedor", "risco",
     r"PENALIDADE|INIDONE|IMPEDIMENTO DE LICITAR"),
    ("direta", "Contratação direta", "risco",
     r"DISPENSA DE LICITACAO|INEXIGIBILIDADE|CONTRATACAO DIRE|RATIFICACAO"),
    ("rescisao", "Rescisão contratual", "risco",
     r"RESCISAO"),
    ("errata", "Errata / retificação", "risco",
     r"ERRATA|RETIFICAC"),
    ("aditivo", "Termo aditivo / reequilíbrio", "dinheiro",
     r"TERMO ADITIVO|REEQUILIBRIO|REPACTUAC|APOSTILAMENTO"),
    ("convenio", "Convênio / termo de colaboração", "dinheiro",
     r"CONVENIO|TERMO DE COLABORACAO|TERMO DE FOMENTO"),
]
GATILHOS = [(k, r, g, re.compile(p)) for k, r, g, p in GATILHOS]

ROTULOS = {k: r for k, r, _, _ in GATILHOS}
ROTULOS["credito"] = "Crédito suplementar (decreto)"
ROTULOS["decreto"] = "Decreto do Poder Executivo"
ROTULOS["segov"] = "SEGOV e as Regionais"
GRUPOS = {k: g for k, _, g, _ in GATILHOS}
GRUPOS.update({"credito": "dinheiro", "decreto": "governo", "segov": "governo"})

RE_CREDITO = re.compile(r"CREDITO SUPLEMENTAR|CREDITO ESPECIAL|CREDITO EXTRAORDINARIO")
RE_VALOR = re.compile(r"R\$ ?(\d{1,3}(?:\.\d{3})*,\d{2})")
RE_SEI = re.compile(r"\b\d{5}-\d{8}/\d{4}-\d{2}\b")
RE_CNPJ = re.compile(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}[-\u2212]\d{2}\b")

CO_PODER_EXECUTIVO = "602"
CO_SEGOV = "606"


def sinais_da_materia(m, trilha=""):
    """Chaves dos sinais que este ato dispara, pela listagem."""
    alvo = normalizar((m.get("titulo") or "") + " " + (m.get("tipo") or ""))
    achados = [k for k, _, _, rx in GATILHOS if rx.search(alvo)]
    co = str(m.get("coDemandante") or "")
    if co == CO_PODER_EXECUTIVO:
        achados.append("decreto")
    if co == CO_SEGOV or "SEGOV" in (trilha or ""):
        achados.append("segov")
    return achados


def eh_credito_suplementar(html_inteiro_teor):
    return bool(RE_CREDITO.search(normalizar(html_inteiro_teor)))


# O cabeçalho do site ocupa os ~6.200 primeiros caracteres da página do ato
# (o formulário de busca inteiro). Sem cortá-lo, a extração lê o formulário
# junto com o ato e devolve campos que não pertencem a ele.
RE_ABRE = re.compile(r"Secretaria Executiva de Atos Oficiais|Se[çc][ãa]o I{1,3} >>")
RE_FECHA = re.compile(r"ORDIN[ÁA]RIA - N|EDI[ÇC][ÃA]O EXTRA - N|Principal Home di[áa]rio")


def texto_limpo(html):
    """Só o corpo do ato: sem o cabeçalho do site, sem o rodapé."""
    t = re.sub(r"<script[\s\S]*?</script>", " ", html)
    t = re.sub(r"<style[\s\S]*?</style>", " ", t)
    t = re.sub(r"<[^>]*>", " ", t)
    t = t.replace("&nbsp;", " ").replace("&amp;", "&")
    t = re.sub(r"\s+", " ", t)
    abre = RE_ABRE.search(t)
    if abre:
        t = t[abre.start():]
    fecha = RE_FECHA.search(t)
    return t[: fecha.start()] if fecha else t


def tem_corpo(texto):
    """Falso quando o ato foi publicado como imagem: não há texto a extrair."""
    return len(texto.strip()) > 400


def campos(texto):
    """Processo SEI, CNPJ e valor. Medidos em 80%, 73% e 66% dos atos."""
    sei = RE_SEI.search(texto)
    cnpj = RE_CNPJ.search(texto)
    val = re.search(r"no valor de R\$ ?(\d{1,3}(?:\.\d{3})*,\d{2})", texto) or RE_VALOR.search(texto)
    return {
        "sei": sei.group(0) if sei else None,
        "cnpj": cnpj.group(0) if cnpj else None,
        "valor": val.group(1) if val else None,
    }


def para_numero(valor_br):
    if not valor_br:
        return None
    return float(valor_br.replace(".", "").replace(",", "."))
