# Como começar — checklist da primeira semana

Ordem importa. Cada item de baixo depende do de cima.

## Dia 1 — Ambiente

- [ ] Instalar Python 3.12 (marcar "Add to PATH" no Windows)
- [ ] Instalar VS Code e Git
- [ ] Criar o ambiente virtual e instalar `requirements.txt`
- [ ] Copiar `config.example.yaml` para `config.yaml` e apontar para o corpus
- [ ] Rodar `pytest -q` e ver quatro testes passando
- [ ] Abrir a pasta no VS Code e aceitar as extensões recomendadas

## Dia 1 — Repositório

- [ ] `git init`
- [ ] `git add .` e conferir com `git status --short` que **nenhum PDF aparece**
- [ ] Primeiro commit
- [ ] Criar o repositório remoto **privado** e dar push

Privado, não público. O corpus não vai junto, mas até a especificação de
anotação é material do seu TCC não publicado.

## Dia 2 — Corpus

- [ ] Baixar o corpus do Drive para `data/raw/` (ou para uma pasta fora do
      projeto, e apontar o `config.yaml` para lá — melhor se o corpus for grande)
- [ ] Rodar `python scripts/01_inventario.py`
- [ ] Ler `relatorios/anomalias.txt` inteiro
- [ ] Corrigir: pastas de junho duplicadas, arquivos que não são jornal,
      acentos em nome de pasta
- [ ] Rodar o inventário de novo e confirmar que as anomalias sumiram

## Dia 2 — Licenciamento

- [ ] Escrever ao *Diário do Comércio* pedindo autorização de uso acadêmico
- [ ] Guardar cópia do envio em `docs/licenciamento/`

Este é o item com maior tempo de espera e você não controla a resposta.
Mande antes de tudo que depende dela.

## Dia 3 a 5 — Orientador

- [ ] Agendar a conversa
- [ ] Levar: tema, artigo-base, corpus, as três opções de escopo
- [ ] Levar as seis perguntas da seção 11 do plano de execução
- [ ] Sair com um escopo aprovado e a data real de entrega

Sem escopo aprovado, não comece a Fase 1.

## Sinais de que deu certo

Ao fim da semana você deve ter: ambiente rodando, repositório privado com
histórico, inventário limpo sem anomalias pendentes, e-mail de licenciamento
enviado, e escopo aprovado por escrito.

Nada disso é código de pesquisa. É fundação. Pular qualquer um desses itens
custa mais caro depois do que custa agora.
