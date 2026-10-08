"""A árvore de órgãos, como o DODF a entrega.

Duas lições medidas:
  - O nome engana; a trilha não. "Diretoria de Saúde" tem trilha
    SSPDF > CBMDF — é Bombeiros, não Secretaria de Saúde.
  - O código raiz não cobre os filhos. Para pegar uma secretaria inteira
    é preciso olhar o `rastreio`, não o código isolado.
"""


def achatar(demandantes, saida=None, raiz=None):
    """Percorre a árvore e devolve {codigo: {nome, trilha, sigla_raiz}}."""
    if saida is None:
        saida = {}
    for co, v in (demandantes or {}).items():
        rastreio = v.get("rastreio") or []
        saida[str(co)] = {
            "nome": v.get("ds_nome") or "",
            "trilha": " > ".join(rastreio),
            "raiz": rastreio[0] if rastreio else None,
        }
        if raiz and rastreio:
            saida.setdefault("_siglas", {})[raiz] = rastreio[0]
        if v.get("filhos"):
            achatar(v["filhos"], saida, raiz or str(co))
    return saida


def sigla(codigo, mapa):
    """A que secretaria este órgão pertence."""
    info = mapa.get(str(codigo)) or {}
    if info.get("raiz"):
        return info["raiz"]
    return (mapa.get("_siglas") or {}).get(str(codigo)) or info.get("nome") or str(codigo)
