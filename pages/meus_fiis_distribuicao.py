import sys, os, json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import pandas as pd
import plotly.express as px
from src.get_fiis import get_data
from src.constants import MY_TICKERS

st.set_page_config(page_title='Meus FIIs - Distribuição', layout='wide')

# Carrega os dados dos FIIs
df = get_data()
my_fiis_df = df[df['Ticker'].isin(MY_TICKERS)].copy()

st.title('📊 Meus FIIs - Distribuição')

########################################### CARREGAMENTO DAS QUANTIDADES

QUANTITY_FILE = 'my_fiis_quantities.json'

def load_quantities():
    """Carrega as quantidades salvas dos FIIs"""
    if os.path.exists(QUANTITY_FILE):
        with open(QUANTITY_FILE, 'r') as f:
            return json.load(f)
    return {}

# Carrega as quantidades
quantities = load_quantities()

########################################### VERIFICAÇÃO DE DADOS

if not quantities or all(qty == 0 for qty in quantities.values()):
    st.warning('⚠️ Nenhuma quantidade de FII foi encontrada!')
    st.info('💡 Acesse a página **"Meus FIIs - Quantidades"** para inserir as quantidades dos seus FIIs.')
    st.stop()

# Filtra apenas FIIs com quantidade > 0
active_fiis = {ticker: qty for ticker, qty in quantities.items() if qty > 0}

if not active_fiis:
    st.warning('⚠️ Nenhum FII com quantidade maior que zero encontrado!')
    st.info('💡 Acesse a página **"Meus FIIs - Quantidades"** para inserir as quantidades dos seus FIIs.')
    st.stop()

########################################### RESUMO GERAL

st.header('📈 Resumo Geral')

col1, col2, col3, col4 = st.columns(4)

# Calcula métricas gerais
total_investido = sum(qty * my_fiis_df[my_fiis_df['Ticker'] == ticker].iloc[0]['Cotação'] 
                     for ticker, qty in active_fiis.items() 
                     if not my_fiis_df[my_fiis_df['Ticker'] == ticker].empty)

total_cotas = sum(active_fiis.values())
total_fiis = len(active_fiis)

# Calcula DY médio ponderado
dy_ponderado = 0
for ticker, qty in active_fiis.items():
    fii_data = my_fiis_df[my_fiis_df['Ticker'] == ticker]
    if not fii_data.empty:
        valor_fii = qty * fii_data.iloc[0]['Cotação']
        dy_fii = fii_data.iloc[0]['Dividend Yield']
        dy_ponderado += (valor_fii / total_investido) * dy_fii

with col1:
    st.metric("Total Investido", f"R$ {total_investido:,.2f}".replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.'))
with col2:
    st.metric("Total de Cotas", f"{total_cotas:,}".replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.'))
with col3:
    st.metric("FIIs na Carteira", f"{total_fiis}")
with col4:
    st.metric("DY Médio Ponderado", f"{dy_ponderado:.2f}%".replace('.', ','))

########################################### GRÁFICO DE DISTRIBUIÇÃO POR SEGMENTO

st.header('🥧 Distribuição por Segmento')

# Calcula o valor por segmento
segmento_data = {}
for ticker, qty in active_fiis.items():
    fii_data = my_fiis_df[my_fiis_df['Ticker'] == ticker]
    if not fii_data.empty:
        segmento = fii_data.iloc[0]['Segmento']
        cotacao = fii_data.iloc[0]['Cotação']
        valor_total = qty * cotacao
        
        if segmento in segmento_data:
            segmento_data[segmento] += valor_total
        else:
            segmento_data[segmento] = valor_total

if segmento_data:
    # Cria DataFrame para o gráfico
    df_segmento = pd.DataFrame(list(segmento_data.items()), columns=['Segmento', 'Valor Total'])
    df_segmento = df_segmento.sort_values('Valor Total', ascending=False)
    
    # Calcula percentuais
    df_segmento['Percentual'] = (df_segmento['Valor Total'] / df_segmento['Valor Total'].sum() * 100).round(2)
    
    # Cria o gráfico de pizza
    fig_pizza = px.pie(
        df_segmento, 
        values='Valor Total', 
        names='Segmento',
        title='Distribuição do Patrimônio por Segmento',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    # Personaliza o gráfico
    fig_pizza.update_traces(
        textposition='inside', 
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>' +
                     'Valor: R$ %{value:,.2f}<br>' +
                     'Percentual: %{percent}<br>' +
                     '<extra></extra>'
    )
    
    fig_pizza.update_layout(
        font=dict(size=14),
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.01
        )
    )
    
    st.plotly_chart(fig_pizza, use_container_width=True)

########################################### GRÁFICO DE BARRAS POR FII

st.header('📊 Distribuição por FII')

# Prepara dados para gráfico de barras
fiis_data = []
for ticker, qty in active_fiis.items():
    fii_data = my_fiis_df[my_fiis_df['Ticker'] == ticker]
    if not fii_data.empty:
        fii_row = fii_data.iloc[0]
        valor_total = qty * fii_row['Cotação']
        percentual = (valor_total / total_investido) * 100
        
        fiis_data.append({
            'Ticker': ticker,
            'Segmento': fii_row['Segmento'],
            'Valor Total': valor_total,
            'Percentual': percentual,
            'Quantidade': qty,
            'Cotação': fii_row['Cotação'],
            'DY': fii_row['Dividend Yield']
        })

df_fiis = pd.DataFrame(fiis_data)
df_fiis = df_fiis.sort_values('Valor Total', ascending=False)

# Cria gráfico de barras
fig_barras = px.bar(
    df_fiis,
    x='Valor Total',
    y='Ticker',
    color='Segmento',
    title='Valor Investido por FII',
    color_discrete_sequence=px.colors.qualitative.Set3,
    orientation='h'
)

# Prepara os dados para o tooltip de forma mais robusta
customdata_list = []
for _, row in df_fiis.iterrows():
    customdata_list.append([
        row['Segmento'],
        int(row['Quantidade']),
        float(row['DY'])
    ])

fig_barras.update_traces(
    hovertemplate='<b>%{y}</b><br>' +
                 'Valor: R$ %{x:,.2f}<br>' +
                 'Segmento: %{customdata[0]}<br>' +
                 'Quantidade: %{customdata[1]}<br>' +
                 'DY: %{customdata[2]:.2f}%<br>' +
                 '<extra></extra>',
    customdata=customdata_list
)

fig_barras.update_layout(
    xaxis_title='Valor Investido (R$)',
    yaxis_title='FII',
    font=dict(size=12)
)

st.plotly_chart(fig_barras, use_container_width=True)

########################################### TABELAS DETALHADAS

col1, col2 = st.columns(2)

with col1:
    st.subheader('📋 Resumo por Segmento')
    
    # Formata os valores para exibição
    df_display = df_segmento.copy()
    df_display['Valor Total'] = df_display['Valor Total'].apply(
        lambda x: f"R$ {x:,.2f}".replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.')
    )
    df_display['Percentual'] = df_display['Percentual'].apply(
        lambda x: f"{x:.2f}%".replace('.', ',')
    )
    
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True
    )

with col2:
    st.subheader('🔍 Detalhamento por FII')
    
    # Formata dados dos FIIs para exibição
    df_fiis_display = df_fiis.copy()
    df_fiis_display['Valor Total'] = df_fiis_display['Valor Total'].apply(
        lambda x: f"R$ {x:,.2f}".replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.')
    )
    df_fiis_display['Percentual'] = df_fiis_display['Percentual'].apply(
        lambda x: f"{x:.2f}%".replace('.', ',')
    )
    df_fiis_display['Cotação'] = df_fiis_display['Cotação'].apply(
        lambda x: f"R$ {x:.2f}".replace('.', ',')
    )
    df_fiis_display['DY'] = df_fiis_display['DY'].apply(
        lambda x: f"{x:.2f}%".replace('.', ',')
    )
    
    # Seleciona colunas para exibição
    df_fiis_display = df_fiis_display[['Ticker', 'Segmento', 'Quantidade', 'Cotação', 'Valor Total', 'Percentual', 'DY']]
    
    st.dataframe(
        df_fiis_display,
        use_container_width=True,
        hide_index=True
    )

########################################### ANÁLISE DE PERFORMANCE

st.header('📈 Análise de Performance')

# Calcula métricas por segmento
segmento_metrics = {}
for ticker, qty in active_fiis.items():
    fii_data = my_fiis_df[my_fiis_df['Ticker'] == ticker]
    if not fii_data.empty:
        fii_row = fii_data.iloc[0]
        segmento = fii_row['Segmento']
        valor_fii = qty * fii_row['Cotação']
        
        if segmento not in segmento_metrics:
            segmento_metrics[segmento] = {
                'valor_total': 0,
                'dy_ponderado': 0,
                'pvp_ponderado': 0,
                'fiis_count': 0
            }
        
        peso = valor_fii / total_investido
        segmento_metrics[segmento]['valor_total'] += valor_fii
        segmento_metrics[segmento]['dy_ponderado'] += peso * fii_row['Dividend Yield']
        segmento_metrics[segmento]['pvp_ponderado'] += peso * fii_row['P/VP']
        segmento_metrics[segmento]['fiis_count'] += 1

# Cria DataFrame com métricas por segmento
metrics_data = []
for segmento, metrics in segmento_metrics.items():
    metrics_data.append({
        'Segmento': segmento,
        'Valor Total': f"R$ {metrics['valor_total']:,.2f}".replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.'),
        'DY Médio': f"{metrics['dy_ponderado']:.2f}%".replace('.', ','),
        'P/VP Médio': f"{metrics['pvp_ponderado']:.2f}".replace('.', ','),
        'Qtd FIIs': metrics['fiis_count']
    })

df_metrics = pd.DataFrame(metrics_data)
df_metrics = df_metrics.sort_values('Valor Total', ascending=False)

st.dataframe(
    df_metrics,
    use_container_width=True,
    hide_index=True
)

########################################### INFORMAÇÕES ADICIONAIS

st.sidebar.header('ℹ️ Informações')
st.sidebar.info(
    "Esta página mostra a distribuição e análise do seu patrimônio em FIIs. "
    "Para atualizar as quantidades, acesse a página 'Meus FIIs - Quantidades'."
)

# Mostra data de atualização dos dados
if not my_fiis_df.empty:
    atualizado = my_fiis_df['Data Atualização'].min().strftime('%d/%m/%Y %Hh%Mmin')
    st.sidebar.text(f'Dados atualizados em: {atualizado}')

# Link para a página de quantidades
st.sidebar.markdown("---")
st.sidebar.markdown("### ✏️ Editar Quantidades")
st.sidebar.markdown("Para alterar as quantidades dos seus FIIs, acesse a página **'Meus FIIs - Quantidades'**.")
