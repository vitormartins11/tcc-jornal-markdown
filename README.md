# Conversão de páginas de jornal diagramado em Markdown estruturado

TCC. Comparação de estratégias de especialização de modelos de visão e
linguagem para converter páginas de jornal em Markdown que preserve estrutura:
hierarquia de títulos, separação entre matérias, ordem de leitura entre colunas.

**Corpus:** *Diário do Comércio* (Belo Horizonte), janeiro a junho de 2025.
PDFs nativos de Adobe InDesign com camada de texto completa.

**Artigo-base metodológico:** TAN, Jin Khye et al. *Fine-Tuning Vision-Language
Models for Markdown Conversion of Financial Tables in Malaysian Audited
Financial Reports*. arXiv:2508.05669, 2025.

---

## Instalação

Precisa de Python 3.11 ou 3.12 e Git.

### 1. Clone ou copie o projeto e entre na pasta

```bash
cd tcc-jornal-markdown
```

### 2. Crie o ambiente virtual

**Windows (PowerShell):**
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Se o PowerShell bloquear o script de ativação:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

**Linux / macOS:**
```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

O prompt passa a mostrar `(.venv)`. Se não mostrar, o ambiente não ativou.

### 3. Instale as dependências

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure o caminho do corpus

```bash
cp config/config.example.yaml config/config.yaml     # Linux/macOS
copy config\config.example.yaml config\config.yaml   # Windows
```

Abra `config/config.yaml` e troque `MUDE_AQUI` pelo caminho da pasta onde você
baixou o corpus. Use barras normais mesmo no Windows.

### 5. Confira que funcionou

```bash
pytest -q
```

Seis testes devem passar. Se passarem, o ambiente está pronto.

---

## VS Code

Abra a **pasta do projeto** (`File > Open Folder`), não um arquivo solto — as
configurações em `.vscode/` só valem assim.

Ao abrir, o VS Code sugere as extensões recomendadas. Aceite. São elas:

| Extensão | Para quê |
|---|---|
| Python + Pylance | linguagem, autocomplete, tipos |
| Ruff | formatação e lint automáticos ao salvar |
| Jupyter | notebooks de exploração |
| PDF Viewer | abrir os PDFs do corpus dentro do editor |
| Rainbow CSV | ler o inventário sem sair do editor |
| Markdown All in One | escrever a documentação |
| GitLens | histórico do repositório |

Selecione o interpretador: `Ctrl+Shift+P` → *Python: Select Interpreter* →
escolha o que está dentro de `.venv`.

Há duas configurações de execução prontas em `Run and Debug` (`Ctrl+Shift+D`):
"Inventário do corpus" e "Arquivo atual".

---

## Organização das pastas

```
tcc-jornal-markdown/
├── config/           configuração (config.yaml é local, não vai para o Git)
├── data/             CORPUS — nunca versionado
│   ├── raw/          original, somente leitura
│   ├── interim/      intermediários, descartáveis
│   └── processed/    dataset final, faça backup
├── src/              código reutilizável, importável
│   ├── inventario/   varredura e higiene do corpus
│   ├── gabarito/     extração de estrutura do PDF nativo   [Fase 2]
│   ├── metricas/     avaliação em camadas                  [Fase 1]
│   ├── baselines/    execução dos conversores existentes   [Fase 3]
│   └── utils/        configuração e utilidades
├── scripts/          entradas executáveis, numeradas na ordem de uso
├── tests/            testes automatizados
├── notebooks/        exploração e gráficos
├── relatorios/       saídas de diagnóstico (regeráveis)
├── resultados/       métricas dos experimentos (regeráveis)
└── docs/             plano, especificação de anotação, licenciamento
```

**A regra de ouro:** `src/` tem funções, `scripts/` tem entradas. Nada que
esteja em `scripts/` deve conter lógica que você queira reaproveitar.

---

## Ordem de execução

```bash
python scripts/01_inventario.py
```

Gera `relatorios/inventario.csv`, `relatorios/inventario_edicoes.csv` e
`relatorios/anomalias.txt`.

**Leia `anomalias.txt` antes de qualquer coisa.** Ele aponta pastas com nome
inconsistente, arquivos que não são página de jornal, PDFs sem camada de texto
e possíveis duplicatas.

Os próximos scripts entram conforme as fases avançam.

---

## Aviso sobre o corpus

O *Diário do Comércio* é veículo comercial e o conteúdo é protegido por direito
autoral. O `.gitignore` já bloqueia `data/`, mas confira antes do primeiro
`git push`:

```bash
git status --short
```

Se aparecer qualquer `.pdf` ou `.md` do corpus, **pare** e corrija o
`.gitignore` antes de commitar. Uma vez enviado ao GitHub, o histórico guarda
o arquivo mesmo depois de removido.

O que pode ser publicado: código, métricas agregadas, e a especificação de
anotação. O que não pode, sem autorização por escrito: as páginas e o texto
integral.
