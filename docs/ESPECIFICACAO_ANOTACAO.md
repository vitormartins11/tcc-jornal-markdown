# Especificação de Anotação para Jornais em Markdown

**Objetivo:** converter página de jornal em Markdown estruturado que preserve hierarquia editorial, segmentação de matérias e ordem de leitura.

## 1. Hierarquia de Títulos

A hierarquia editorial do *Diário do Comércio* é:

| Nível Editorial | Markdown | Exemplo |
|---|---|---|
| Chapéu (linha fina acima) | `# ` | `# ECONOMIA` |
| Manchete (título principal) | `## ` | `## Copasa é a melhor empresa de saneamento` |
| Olho / Subtítulo | `### ` | `### Crescimento sustentável em foco` |
| Intertítulo (dentro da matéria) | `#### ` | `#### Números impressionantes` |
| Legenda (figura, infográfico) | `##### ` | `##### Legenda: Estrutura de saneamento em Minas` |

**Regras:**
- Sempre colocar exatamente um espaço após `#`
- Não usar dois `#` de mesmo nível seguidos sem conteúdo entre eles
- Se não há hierarquia clara visual, usar `##` como padrão para matérias

## 2. Estrutura de Matéria

Cada matéria é um bloco coeso que inclui:

```markdown
## Título da Matéria

Parágrafo introdutório.

Segundo parágrafo.

### Intertítulo (se houver)

Mais conteúdo.
```

**Separação entre matérias:** duas linhas em branco entre matérias independentes.

Exemplo:
```markdown
## Matéria 1

Conteúdo da matéria 1.


## Matéria 2

Conteúdo da matéria 2.
```

## 3. Ordem de Leitura

A ordem de leitura deve seguir a **disposição visual** da página, não a ordem alfabética ou por importância. Se a página tem colunas:
