"""Consolida os .trx de várias execuções (job "build" e job "integration") num único resumo de testes.

Cada teste é identificado por (alvo, nome). Quando o mesmo teste aparece em mais de uma execução, vale o resultado mais
forte: Failed > Passed > NotExecuted. Assim, um teste de integração pulado no "build" (sem acesso ao cofre) e executado
no "integration" conta como aprovado no relatório.

Uso: python3 resumo-testes.py <pasta-com-trx> [arquivo-markdown-de-saída] [--ignorar PADRÃO ...]
     --ignorar: padrões (fnmatch) de nomes de .trx fora do relatório, ex.: 'TEC.Vault.LoadTests*' (testes de carga).
Sai com código 0 sempre: quem quebra o pipeline são os jobs de teste; este script só relata.
"""

import argparse
import fnmatch
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {"t": "http://microsoft.com/schemas/VisualStudio/TeamTest/2010"}
PRIORIDADE = {"Failed": 3, "Passed": 2, "NotExecuted": 1}
TFM = re.compile(r"[\\/](net\d+\.\d+)[\\/]")


def alvo(storage: str) -> str:
    m = TFM.search(storage or "")
    return m.group(1) if m else "?"


def ler(trx: Path, resultados: dict) -> None:
    raiz = ET.parse(trx).getroot()
    storage = {
        ut.get("id"): ut.get("storage", "")
        for ut in raiz.iterfind("t:TestDefinitions/t:UnitTest", NS)
    }
    for r in raiz.iterfind("t:Results/t:UnitTestResult", NS):
        outcome = r.get("outcome", "NotExecuted")
        if outcome not in PRIORIDADE:
            outcome = "Failed" if outcome in ("Error", "Timeout", "Aborted") else "NotExecuted"
        chave = (alvo(storage.get(r.get("testId"), "")), r.get("testName", "?"))
        motivo = ""
        if outcome == "NotExecuted":
            # TUnit grava o motivo em DebugTrace ("Skipped: <motivo>"); outros frameworks, em ErrorInfo/StdOut
            for caminho in ("t:Output/t:DebugTrace", "t:Output/t:ErrorInfo/t:Message", "t:Output/t:StdOut"):
                msg = r.find(caminho, NS)
                if msg is not None and (msg.text or "").strip():
                    motivo = msg.text.strip().splitlines()[0].removeprefix("Skipped: ")
                    break
        atual = resultados.get(chave)
        if atual is None or PRIORIDADE[outcome] > PRIORIDADE[atual[0]]:
            resultados[chave] = (outcome, motivo)


def main() -> int:
    args = argparse.ArgumentParser()
    args.add_argument("pasta", type=Path)
    args.add_argument("saida", type=Path, nargs="?")
    args.add_argument("--ignorar", action="append", default=[])
    a = args.parse_args()
    pasta, saida = a.pasta, a.saida
    resultados: dict = {}
    arquivos = sorted(
        t for t in pasta.rglob("*.trx") if not any(fnmatch.fnmatch(t.name, padrao) for padrao in a.ignorar)
    )
    for trx in arquivos:
        ler(trx, resultados)

    contagem = {"Passed": 0, "Failed": 0, "NotExecuted": 0}
    for outcome, _ in resultados.values():
        contagem[outcome] += 1

    linhas = [
        "### 🧪 Testes (unitários + integração)",
        "",
        f"Consolidado de {len(arquivos)} arquivo(s) .trx. Teste pulado num job e executado em outro conta como executado.",
        "",
        "| Total | ✅ Aprovados | ❌ Falhas | ⏭️ Pulados |",
        "|---:|---:|---:|---:|",
        f"| {len(resultados)} | {contagem['Passed']} | {contagem['Failed']} | {contagem['NotExecuted']} |",
        "",
    ]
    for titulo, outcome in (("❌ Falhas", "Failed"), ("⏭️ Pulados", "NotExecuted")):
        itens = sorted((k, v) for k, v in resultados.items() if v[0] == outcome)
        if not itens:
            continue
        linhas += [f"<details><summary>{titulo} ({len(itens)})</summary>", "", "| Alvo | Teste | Motivo |", "|---|---|---|"]
        for (tfm, nome), (_, motivo) in itens[:200]:
            linhas.append(f"| {tfm} | `{nome}` | {motivo.replace('|', '/')} |")
        linhas += ["", "</details>", ""]

    texto = "\n".join(linhas) + "\n"
    print(texto)
    if saida:
        with saida.open("a", encoding="utf-8") as f:
            f.write(texto)
    return 0


if __name__ == "__main__":
    sys.exit(main())
