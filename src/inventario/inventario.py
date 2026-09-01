#!/usr/bin/env python3
"""
Inventário e higiene do corpus — Fase 0.4

Módulo. Para rodar pela linha de comando, use scripts/01_inventario.py.

Varre a árvore de pastas do corpus, extrai metadados de cada PDF e gera:
  - inventario.csv       : uma linha por página, com metadados técnicos
  - inventario_edicoes.csv : uma linha por edição
  - anomalias.txt        : arquivos e pastas que precisam de atenção

"""

import csv
import hashlib
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

try:
    import pymupdf as fitz
except ImportError:
    sys.exit("Instale a dependência primeiro:  pip install pymupdf")


# --------------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------------

MESES = {
    "JANEIRO": 1, "FEVEREIRO": 2, "MARCO": 3, "MARÇO": 3, "ABRIL": 4,
    "MAIO": 5, "JUNHO": 6, "JULHO": 7, "AGOSTO": 8, "SETEMBRO": 9,
    "OUTUBRO": 10, "NOVEMBRO": 11, "DEZEMBRO": 12,
}


def sem_acento(texto: str) -> str:
    """Remove acentos para comparação e para sugerir nome de pasta em ASCII."""
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def md5_curto(caminho: Path, blocos: int = 8) -> str:
    """Hash dos primeiros blocos do arquivo — suficiente para achar duplicata."""
    h = hashlib.md5()
    with open(caminho, "rb") as f:
        for _ in range(blocos):
            pedaco = f.read(65536)
            if not pedaco:
                break
            h.update(pedaco)
    return h.hexdigest()[:12]


def parse_pasta_mes(nome: str):
    """'04 - ABRIL DE 2025' -> (4, 2025). Devolve (None, None) se não casar."""
    limpo = sem_acento(nome).upper()
    m = re.match(r"\s*(\d{1,2})\s*-\s*([A-Z]+)\s+DE\s+(\d{4})", limpo)
    if not m:
        return None, None, None
    prefixo, mes_nome, ano = int(m.group(1)), m.group(2), int(m.group(3))
    return prefixo, MESES.get(mes_nome), ano


def parse_pasta_edicao(nome: str):
    """
    Reconhece:
      'EDIÇÃO DE 17-01-2025'        -> (date(2025,1,17), False)
      'EDIÇÃO DE 05 A 07-04-2025'   -> (date(2025,4,5),  True)   # edição consolidada
    """
    limpo = sem_acento(nome).upper()
    m = re.search(r"(\d{1,2})\s+A\s+(\d{1,2})-(\d{1,2})-(\d{4})", limpo)
    if m:
        d, _, mes, ano = m.groups()
        return f"{ano}-{int(mes):02d}-{int(d):02d}", True
    m = re.search(r"(\d{1,2})-(\d{1,2})-(\d{4})", limpo)
    if m:
        d, mes, ano = m.groups()
        return f"{ano}-{int(mes):02d}-{int(d):02d}", False
    return None, None


def classificar_pagina(n_chars: int, n_imagens: int, nome_arquivo: str,
                       corte_baixo: int, corte_alto: int) -> str:
    """
    Triagem grosseira de tipo de página, só para permitir amostragem
    estratificada depois. NÃO é anotação.

    Os cortes vêm dos percentis 25 e 75 do próprio corpus, calculados em
    segunda passada — assim a classificação se adapta ao veículo em vez de
    depender de limiares fixos.
    """
    if "CAPA" in nome_arquivo.upper():
        return "capa"
    if n_chars < 400:
        return "predominantemente_visual"
    if n_chars >= corte_alto:
        return "densa"
    if n_chars <= corte_baixo:
        return "leve"
    if n_imagens >= 4:
        return "muitas_imagens"
    return "corrida"


# --------------------------------------------------------------------------
# Varredura
# --------------------------------------------------------------------------

def inspecionar_pdf(caminho: Path):
    """Abre o PDF e devolve dicionário de metadados. Nunca levanta exceção."""
    dados = {
        "paginas_pdf": None, "produtor": None, "criador": None,
        "data_criacao": None, "largura_pt": None, "altura_pt": None,
        "chars_texto": None, "n_spans": None, "n_imagens": None,
        "n_fontes": None, "tem_camada_texto": None, "tipo_pagina": None,
        "erro": "",
    }
    try:
        with fitz.open(caminho) as doc:
            meta = doc.metadata or {}
            dados["paginas_pdf"] = doc.page_count
            dados["produtor"] = (meta.get("producer") or "").strip()
            dados["criador"] = (meta.get("creator") or "").strip()
            dados["data_criacao"] = (meta.get("creationDate") or "").strip()

            if doc.page_count == 0:
                dados["erro"] = "pdf sem paginas"
                return dados

            pagina = doc[0]
            dados["largura_pt"] = round(pagina.rect.width, 1)
            dados["altura_pt"] = round(pagina.rect.height, 1)

            texto = pagina.get_text()
            dados["chars_texto"] = len(texto.strip())
            dados["tem_camada_texto"] = dados["chars_texto"] > 100

            bruto = pagina.get_text("dict")
            spans = 0
            fontes = set()
            for bloco in bruto.get("blocks", []):
                for linha in bloco.get("lines", []):
                    for span in linha.get("spans", []):
                        spans += 1
                        fontes.add((span.get("font"), round(span.get("size", 0), 1)))
            dados["n_spans"] = spans
            dados["n_fontes"] = len(fontes)
            dados["n_imagens"] = len(pagina.get_images(full=True))
    except Exception as exc:
        dados["erro"] = f"{type(exc).__name__}: {exc}"[:200]
    return dados


def varrer(raiz: Path, saida: Path):
    linhas = []
    anomalias = []
    por_edicao = defaultdict(lambda: {
        "paginas": 0, "md_divididos": 0, "md_llamaparse": 0,
        "md_outros": 0, "txt": 0, "nao_pdf": [],
    })
    hashes = defaultdict(list)
    pastas_mes = {}

    # --- pastas de mês ---
    for p in sorted(raiz.iterdir()):
        if not p.is_dir():
            continue
        prefixo, mes, ano = parse_pasta_mes(p.name)
        if mes is None:
            anomalias.append(f"[pasta nao reconhecida] {p.name}")
            continue
        chave = (ano, mes)
        if chave in pastas_mes:
            anomalias.append(
                f"[mes duplicado] '{p.name}' e '{pastas_mes[chave]}' apontam para "
                f"{mes:02d}/{ano}. Uma das duas esta com nome errado."
            )
        else:
            pastas_mes[chave] = p.name
        if prefixo != mes:
            anomalias.append(
                f"[prefixo inconsistente] '{p.name}': prefixo {prefixo:02d} "
                f"nao corresponde ao mes {mes:02d}."
            )
        if p.name != sem_acento(p.name):
            anomalias.append(f"[acento no nome] {p.name} -> sugerido: {sem_acento(p.name)}")

    # --- arquivos ---
    for caminho in sorted(raiz.rglob("*")):
        if caminho.is_dir():
            if caminho.name != sem_acento(caminho.name):
                anomalias.append(
                    f"[acento no nome] {caminho.relative_to(raiz)} -> "
                    f"sugerido: {sem_acento(caminho.name)}"
                )
            continue

        rel = caminho.relative_to(raiz)
        partes = rel.parts
        ext = caminho.suffix.lower()

        pasta_edicao = next((x for x in partes if "DE " in sem_acento(x).upper()), None)
        data_ed, consolidada = parse_pasta_edicao(pasta_edicao or "")
        id_edicao = data_ed or (pasta_edicao or "SEM_EDICAO")

        # arquivos que não deveriam estar aqui
        if ext not in {".pdf", ".md", ".txt"}:
            por_edicao[id_edicao]["nao_pdf"].append(str(rel))
            anomalias.append(f"[arquivo estranho] {rel}")
            continue

        if ext == ".md":
            if "LlamaParse" in partes:
                por_edicao[id_edicao]["md_llamaparse"] += 1
            elif "divididos" in partes:
                por_edicao[id_edicao]["md_divididos"] += 1
            else:
                por_edicao[id_edicao]["md_outros"] += 1
            continue

        if ext == ".txt":
            por_edicao[id_edicao]["txt"] += 1
            continue

        # PDF em subpasta 'divididos' é cópia da página; conta separado
        if "divididos" in partes:
            continue

        info = inspecionar_pdf(caminho)
        h = md5_curto(caminho)
        hashes[h].append(str(rel))

        por_edicao[id_edicao]["paginas"] += 1
        por_edicao[id_edicao]["mes"] = partes[0] if partes else ""
        por_edicao[id_edicao]["consolidada"] = consolidada

        linhas.append({
            "caminho": str(rel),
            "arquivo": caminho.name,
            "pasta_mes": partes[0] if partes else "",
            "pasta_edicao": pasta_edicao or "",
            "data_edicao": data_ed or "",
            "edicao_consolidada": consolidada,
            "tamanho_bytes": caminho.stat().st_size,
            "md5_curto": h,
            **info,
        })

    # classificação de tipo de página, calibrada pelos percentis do corpus
    valores = sorted(l["chars_texto"] for l in linhas if l["chars_texto"] is not None)
    if valores:
        corte_baixo = valores[len(valores) // 4]
        corte_alto = valores[(3 * len(valores)) // 4]
        for l in linhas:
            l["tipo_pagina"] = classificar_pagina(
                l["chars_texto"] or 0, l["n_imagens"] or 0,
                l["arquivo"], corte_baixo, corte_alto)

    # duplicatas
    for h, arquivos in hashes.items():
        if len(arquivos) > 1:
            anomalias.append(f"[possivel duplicata] {h}: " + " | ".join(arquivos))

    # PDFs sem camada de texto
    for l in linhas:
        if l["tem_camada_texto"] is False:
            anomalias.append(f"[sem camada de texto] {l['caminho']}")
        if l["erro"]:
            anomalias.append(f"[erro ao ler] {l['caminho']}: {l['erro']}")

    # --- escrita ---
    saida.mkdir(parents=True, exist_ok=True)

    if linhas:
        with open(saida / "inventario.csv", "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=list(linhas[0].keys()))
            w.writeheader()
            w.writerows(linhas)

    with open(saida / "inventario_edicoes.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["id_edicao", "pasta_mes", "consolidada", "paginas_pdf",
                    "md_divididos", "md_llamaparse", "md_outros", "txt",
                    "arquivos_estranhos"])
        for k in sorted(por_edicao):
            d = por_edicao[k]
            w.writerow([k, d.get("mes", ""), d.get("consolidada", ""), d["paginas"],
                        d["md_divididos"], d["md_llamaparse"], d["md_outros"],
                        d["txt"], len(d["nao_pdf"])])

    with open(saida / "anomalias.txt", "w", encoding="utf-8") as f:
        f.write(f"Inventario gerado em {datetime.now():%Y-%m-%d %H:%M}\n")
        f.write(f"Raiz: {raiz}\n")
        f.write(f"Total de anomalias: {len(anomalias)}\n\n")
        for a in anomalias:
            f.write(a + "\n")

    # --- resumo no terminal ---
    print(f"\nPáginas PDF inventariadas : {len(linhas)}")
    print(f"Edições encontradas       : {len(por_edicao)}")
    print(f"Anomalias registradas     : {len(anomalias)}")

    if linhas:
        produtores = Counter(l["produtor"] for l in linhas)
        criadores = Counter(l["criador"] for l in linhas)
        tipos = Counter(l["tipo_pagina"] for l in linhas)
        dims = Counter((l["largura_pt"], l["altura_pt"]) for l in linhas)
        sem_texto = sum(1 for l in linhas if l["tem_camada_texto"] is False)

        print("\nProdutor do PDF:")
        for k, v in produtores.most_common(5):
            print(f"  {v:5}  {k or '(vazio)'}")
        print("\nCriador do PDF:")
        for k, v in criadores.most_common(5):
            print(f"  {v:5}  {k or '(vazio)'}")
        print("\nTipo de página (triagem heurística):")
        for k, v in tipos.most_common():
            print(f"  {v:5}  {k}")
        print("\nDimensões (pt):")
        for k, v in dims.most_common(5):
            print(f"  {v:5}  {k[0]} x {k[1]}")
        print(f"\nPáginas sem camada de texto: {sem_texto}")

    print(f"\nArquivos gerados em: {saida.resolve()}")
    print("  inventario.csv")
    print("  inventario_edicoes.csv")
    print("  anomalias.txt")
    print("\nLeia anomalias.txt ANTES de processar qualquer coisa em lote.\n")
