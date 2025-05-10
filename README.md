# FIIs Buscador

### Deploy Local

#### Utilizando pyenv e venv

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
python3 src/scrapes/fundamentus.py
python3 src/scrapes/investidor10.py
python3 src/scrapes/fnet.py
~~~

Inicializar projeto local
~~~sh
streamlit run buscador.py
~~~
