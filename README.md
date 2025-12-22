# FIIs Buscador

### Deploy Local utilizando Linux

#### Utilizando pyenv e venv

Fácil instalação do pyenv, caso ainda não tenha
~~~sh
curl -fsSL https://pyenv.run | bash
~~~

Instalar versão 3.10.12 do python, caso ainda não tenha
~~~sh
pyenv install $(pyenv local)
~~~

Criar e usar ambiente virtual
~~~sh
python3 -m venv .venv

source .venv/bin/activate
~~~

Instalar libs de dependência
~~~sh
pip install -r requirements.txt
~~~

Fazer scrapes local
~~~sh
python3 src/scrapes/all_scrapes.py
~~~

Inicializar projeto local
~~~sh
streamlit run buscador.py
~~~

## Linting e Formatação

Este projeto utiliza ferramentas de lint e formatação para manter o código consistente e de qualidade.

### Instalação das ferramentas

As ferramentas já estão incluídas no `requirements.txt`. Após instalar as dependências, você terá acesso a:

- **flake8**: Verifica estilo de código e erros comuns
- **black**: Formata o código automaticamente
- **isort**: Organiza os imports alfabeticamente

### Como usar

#### Verificar problemas de estilo (sem corrigir)
~~~sh
flake8 .
~~~

#### Formatar código automaticamente com black
~~~sh
black .
~~~

#### Organizar imports com isort
~~~sh
isort .
~~~

#### Executar todas as verificações e formatações
~~~sh
# Formatar código
black .

# Organizar imports
isort .

# Verificar problemas restantes
flake8 .
~~~

### Configuração

- **`.flake8`**: Configurações do flake8 (tamanho máximo de linha, erros a ignorar, etc.)
- **`pyproject.toml`**: Configurações do black e isort

### O que é lint?

**Lint** são ferramentas que analisam seu código procurando por:
- Problemas de estilo (espaçamento, indentação, etc.)
- Erros comuns (variáveis não usadas, imports não utilizados)
- Más práticas de programação
- Complexidade excessiva
- Conformidade com padrões (PEP 8 para Python)

Isso ajuda a manter o código limpo, legível e consistente em todo o projeto!
