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
