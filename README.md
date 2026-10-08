# Radar DODF

Lê o Diário Oficial do Distrito Federal todo dia útil, separa o que pede atenção
do que é rotina e publica um boletim.

Em 10 dias medidos o DODF publicou **3.864 atos** — 386 por dia. A peneira reduz a
cerca de **59 por dia**. É a diferença entre um diário e uma pauta.

## Como roda

```bash
python -m radar.coleta             # edição de hoje
python -m radar.coleta 2026-10-08  # uma data específica
```

Sem dependências: só a biblioteca padrão do Python. O resultado vai para
`dados/AAAA-MM-DD.json` e `dados/ultimo.json`, que é o que a página lê.

O GitHub Actions roda às **13:00 e 22:00 UTC** em dias úteis — 10h e 19h de
Brasília, que é UTC-3 o ano todo desde o fim do horário de verão em 2019.
A segunda rodada existe porque houve **edição extra em 8 dos 10 dias** medidos,
e ela traz o que foi decidido ao longo do expediente.

## O contrato da API

Medido contra o servidor em 08/10/2026, não inferido de documentação.

| Rota | O que devolve |
|---|---|
| `POST /dodf/jornal/indicador` | calendário do mês: `{"20261008":["integra","extra"]}` |
| `POST /dodf/jornal/diario` | a edição do dia, paginada de 10 em 10 |
| `GET /dodf/materia/visualizar?co_data=&p=` | o inteiro teor de um ato |

### Armadilhas que custaram descoberta

- **As rotas do DODFMiner estão mortas.** `/index/jornal-json` e `/listar?dir=`
  devolvem 404. Só `/index/visualizar-arquivo/?pasta=&arquivo=` sobreviveu à
  reforma do site. Qualquer desenho apoiado no `jornal-json` não funciona.
- O parâmetro do inteiro teor é **`co_data`**, não `co_materia`. Errar devolve
  204 vazio, sem erro.
- Datas em `yyyy-mm-dd`. O formato brasileiro devolve erro de validação.
- Um `slug` errado **não dá erro**: o servidor devolve a página de busca.
- O cabeçalho do site ocupa os ~6.200 primeiros caracteres da página de um ato.

## A regra da peneira

O gatilho vale quando casa no **título** ou no **tipo** do ato, nunca no corpo.
Buscar no corpo inflava os números entre 22% e 100%: todo contrato cita "dotação
orçamentária" e toda rescisão aparece como cláusula em aditivos que não são rescisões.

**Uma exceção.** Crédito suplementar não tem como casar no título — o título de um
decreto é só o número. E o preâmbulo ("A GOVERNADORA DO DISTRITO FEDERAL, no uso das
atribuições...") consome os ~500 caracteres do trecho da listagem antes de chegar ao
valor. Em 10 dias, **14 dos 17 créditos suplementares eram invisíveis** na listagem.
Por isso a coleta abre o inteiro teor de todo ato sinalizado.

## O que a extração alcança

Medido na edição de 08/10 (88 atos sinalizados de 361):

| Sinal | N | SEI | CNPJ | Valor |
|---|---:|---:|---:|---:|
| Reconhecimento de dívida | 8 | 100% | 100% | 100% |
| Penalidade a fornecedor | 3 | 100% | 100% | 67% |
| Crédito suplementar | 11 | 100% | — | 100% |
| Contratação direta | 12 | 83% | 8% | 83% |
| Termo aditivo | 19 | 89% | 47% | 53% |
| Decreto do Executivo | 16 | 75% | — | 69% |
| Errata / retificação | 12 | 50% | — | — |

Os traços não são falhas: um decreto não tem CNPJ de fornecedor, uma errata não tem
valor. Os 8% de CNPJ em contratação direta são em boa parte corretos — um *aviso* de
contratação é publicado antes de haver fornecedor escolhido.

## O que este radar não vê

- **O TCDF não publica no DODF** como órgão demandante. As matérias que o citam são
  de outros órgãos cumprindo decisão dele. Acompanhar o Tribunal exige a fonte própria.
- **Atos de pessoal estão subcontados.** Nomeações e exonerações raramente usam esses
  verbos no texto visível.
- **Alguns atos são publicados como imagem.** Deles não se extrai processo, CNPJ nem valor.
- **Nome de órgão engana; trilha não.** "Diretoria de Saúde" tem trilha `SSPDF > CBMDF` —
  é Corpo de Bombeiros, não Secretaria de Saúde. O agrupamento usa `rastreio`, nunca o nome.

## Publicação

O repositório é servido estático. `index.html` na raiz lê `dados/ultimo.json`.
Na Vercel, sem framework — o mesmo molde dos outros painéis.

**Antes de compartilhar o link:** a proteção padrão da Vercel é SSO, que exige conta
no time. Para quem está fora, trocar por proteção de senha ou apontar um domínio próprio.
