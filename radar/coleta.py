"""Varre a edição do dia, aplica a peneira e grava o JSON do boletim.

    python -m radar.coleta            # edição de hoje
    python -m radar.coleta 2026-10-08 # uma data específica
"""
import datetime
import json
import os
import sys
import time

from . import dodf, orgaos, sinais

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS = os.path.join(RAIZ, "dados")


def timestamp_local(data):
    """Meia-noite de Brasília, em unix timestamp — o que a rota do diário espera."""
    return int(datetime.datetime(data.year, data.month, data.day, 3, 0, 0,
                                 tzinfo=datetime.timezone.utc).timestamp())


def coletar(data):
    ts = timestamp_local(data)
    materias, arvore, confirmada = dodf.diario_completo(ts)
    mapa = orgaos.achatar(arvore)
    print("%s: %d materias (servidor confirmou %s)" % (data, len(materias), confirmada))

    marcados = []
    for m in materias:
        co = str(m.get("coDemandante") or "")
        info = mapa.get(co) or {}
        achados = sinais.sinais_da_materia(m, info.get("trilha", ""))
        if not achados:
            continue
        marcados.append((m, info, achados))

    # O inteiro teor vale para todo ato sinalizado, por dois motivos medidos:
    #   - crédito suplementar: o trecho da listagem esconde 82% deles;
    #   - CNPJ, processo SEI e valor só aparecem no texto completo
    #     (medidos em 73%, 80% e 66% contra 20%, 64% e 37% no trecho).
    print("  abrindo inteiro teor de %d atos sinalizados" % len(marcados))
    for m, info, achados in marcados:
        html = dodf.inteiro_teor(m.get("coMateria"), m.get("slug") or "")
        if not html:
            continue
        m["_texto_cheio"] = sinais.texto_limpo(html)
        if "decreto" in achados and sinais.eh_credito_suplementar(html):
            achados.append("credito")
        time.sleep(dodf.PAUSA)

    atos = []
    for m, info, achados in marcados:
        texto = m.get("_texto_cheio") or (m.get("texto") or "")
        c = sinais.campos(texto)
        atos.append({
            "id": str(m.get("coMateria")),
            "titulo": m.get("titulo") or "",
            "tipo": m.get("tipo") or "",
            "secao": m.get("secao") or "",
            "orgao": info.get("nome") or co,
            "trilha": info.get("trilha") or "",
            "sigla": orgaos.sigla(m.get("coDemandante"), mapa),
            "sinais": sorted(set(achados)),
            "grupos": sorted({sinais.GRUPOS.get(k, "outro") for k in achados}),
            "trecho": (m.get("texto") or "")[:300],
            "link": dodf.link(m.get("coMateria"), m.get("slug") or ""),
            **c,
        })

    atos.sort(key=lambda a: (0 if "risco" in a["grupos"] else
                             1 if "governo" in a["grupos"] else 2, a["orgao"]))
    return {
        "data": data.isoformat(),
        "confirmada": confirmada,
        "colhido_em": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "total_no_diario": len(materias),
        "total_sinalizado": len(atos),
        "por_secao": {s: sum(1 for m in materias if m.get("secao") == s)
                      for s in ("Seção I", "Seção II", "Seção III")},
        "rotulos": sinais.ROTULOS,
        "atos": atos,
    }


def main():
    if len(sys.argv) > 1:
        data = datetime.date.fromisoformat(sys.argv[1])
    else:
        agora = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=3)
        data = agora.date()

    calendario = dodf.edicoes_do_mes()
    chave = data.strftime("%Y%m%d")
    if chave not in calendario:
        print("sem edicao em %s — nada a fazer" % data)
        return 0

    boletim = coletar(data)
    os.makedirs(DADOS, exist_ok=True)
    for nome in (data.isoformat() + ".json", "ultimo.json"):
        caminho = os.path.join(DADOS, nome)
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(boletim, f, ensure_ascii=False, indent=1)
    print("gravado: %d de %d atos sinalizados" %
          (boletim["total_sinalizado"], boletim["total_no_diario"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
