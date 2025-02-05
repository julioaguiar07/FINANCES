import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import requests 
import base64

# Configuração de estilo
st.set_page_config(page_title="Controle Financeiro", layout="wide")
st.markdown(
    '''
    <style>
    .main-container {
        background-color: #f9f9f9;
        padding: 20px;
    }
    .sidebar {
        background-color: #0E2C4E;
        color: white;
    }
    .process-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
        color: #333333;
    }
    .process-card h4 {
        color: #0E2C4E;
        margin: 0;
    }
    .metric-box {
        background-color: #CF8C28;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
    }
    .metric-box h3 {
        margin: 0;
        color: #ffffff;
        font-size: 24px;
        font-weight: bold;
    }
    .metric-box p {
        margin: 0;
        font-size: 20px;
        color: #ffffff;
    }
    .stButton button {
        background-color: #0E2C4E;
        color: white;
        border-radius: 8px;
        padding: 10px 20px;
        font-size: 16px;
    }
    .stButton button:hover {
        background-color: #CF8C28;
    }
    </style>
    ''',
    unsafe_allow_html=True
)

# Conectar ao banco de dados
conn = sqlite3.connect('gestao_processos.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS financeiro (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_processo INTEGER NOT NULL,
    tipo TEXT NOT NULL,  -- Honorário, Pagamento, Despesa
    valor REAL NOT NULL,
    data TEXT NOT NULL,
    descricao TEXT
)
''')

conn.commit()

def get_base64(file_path):
    with open(file_path, "rb") as file:
        encoded = base64.b64encode(file.read()).decode()
    return encoded

background_image = get_base64("fundo.png")

st.markdown(
    f'''
    <style>
        .stApp {{
            background: url("data:image/png;base64,{background_image}");
            background-size: cover;
            background-position: center;
        }}
    </style>
    ''',
    unsafe_allow_html=True
)

TOKEN = "7988620336:AAGjn4jRyz9O_CynuInWFEjwnoY6EDAUpmE"
CHAT_ID = "-1002327026892"

def enviar_mensagem(texto):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": texto}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Verifica se a requisição foi bem-sucedida
        print("Mensagem enviada com sucesso:", response.json())  # Log para depuração
    except requests.exceptions.RequestException as e:
        print("Erro ao enviar mensagem:", e)  # Log para depuração

def excluir_registro_financeiro(id_registro):
    cursor.execute('DELETE FROM financeiro WHERE id = ?', (id_registro,))
    conn.commit()

def adicionar_registro_financeiro(tipo, valor, data, descricao):
    cursor.execute('''
    INSERT INTO financeiro (id_processo, tipo, valor, data, descricao)
    VALUES (?, ?, ?, ?, ?)
    ''', (1, tipo, valor, data, descricao))
    conn.commit()
    # Enviar mensagem via Telegram
    mensagem = f'''
💰 Novo Gasto Adicionado 💰

📋 Processo ID: 1  
📌 Tipo: {tipo}  
💵 Valor: R$ {valor:.2f}  
📅 Data: {data}  
📝 Descrição: {descricao}

⚠️ **Atenção:** Registro financeiro adicionado com sucesso. Verifique as métricas atualizadas.
'''
    enviar_mensagem(mensagem)

def listar_registros_financeiros():
    cursor.execute('SELECT * FROM financeiro')
    return cursor.fetchall()

def calcular_total_financeiro():
    cursor.execute('SELECT tipo, SUM(valor) FROM financeiro GROUP BY tipo')
    return {tipo: total for tipo, total in cursor.fetchall()}

def calcular_gastos_por_mes():
    cursor.execute('''
    SELECT strftime('%Y-%m', data) as mes, SUM(valor) as total
    FROM financeiro
    GROUP BY mes
    ORDER BY mes DESC
    LIMIT 2
    ''')
    return cursor.fetchall()

def calcular_tipo_mais_gasto():
    cursor.execute('''
    SELECT tipo, SUM(valor) as total
    FROM financeiro
    WHERE strftime('%Y-%m', data) = strftime('%Y-%m', 'now')
    GROUP BY tipo
    ORDER BY total DESC
    LIMIT 1
    ''')
    return cursor.fetchone()

# Interface do Streamlit
st.sidebar.title("Controle de Gastos 📂")
st.sidebar.text("Sistema de Gerenciamento")

opcao = st.sidebar.radio("Páginas", ["Visualizar Gastos", "Registrar Gastos"])

if opcao == "Registrar Gastos":
    st.title("Registro de Gastos 💰")
    st.markdown("---")

    # Adicionar Registro Financeiro
    with st.expander("Adicionar Registro Financeiro"):
        tipo = st.selectbox("Tipo", ["Comida", "Uber", "Gasolina", "Compras", "Mercado", "Assinaturas","Lazer"], key="financeiro_tipo")
        valor = st.number_input("Valor", min_value=0.0, key="financeiro_valor")
        data = st.text_input("Data (ex: 2023-09-03)", key="financeiro_data")
        descricao = st.text_input("Descrição", key="financeiro_descricao")
        if st.button("Adicionar Registro", key="financeiro_adicionar"):
            adicionar_registro_financeiro(tipo, valor, data, descricao)
            st.success("Registro financeiro adicionado com sucesso!")

    # Exibir Registros Financeiros
    st.write("### Registros Financeiros")
    registros = listar_registros_financeiros()
    if registros:
        df_financeiro = pd.DataFrame(registros, columns=["ID", "ID Processo", "Tipo", "Valor", "Data", "Descrição"])
        st.dataframe(df_financeiro)

        # Adicionar botão de exclusão para cada registro
        st.write("### Excluir Registro Financeiro")
        id_registro_excluir = st.number_input("ID do Registro para Excluir", min_value=1, key="excluir_registro")
        if st.button("Excluir Registro", key="excluir_registro_botao"):
            excluir_registro_financeiro(id_registro_excluir)
            st.success("Registro financeiro excluído com sucesso!")
            st.button("Recarregar Página")  # Adiciona um botão para recarregar manualmente
    else:
        st.info("Nenhum registro financeiro encontrado.")

if opcao == "Visualizar Gastos":
    st.title("Visualização de Gastos 💰")
    st.markdown("---")
        # Métricas Financeiras
    st.markdown("---")
    st.write("### Métricas Financeiras")
    gastos_por_mes = calcular_gastos_por_mes()
    tipo_mais_gasto = calcular_tipo_mais_gasto()

    col1, col2, col3 = st.columns(3)
    if len(gastos_por_mes) > 1:
        col1.metric("Total Gasto Mês Anterior", f"R$ {gastos_por_mes[1][1]:.2f}")
    else:
        col1.metric("Total Gasto Mês Anterior", "R$ 0.00")

    if len(gastos_por_mes) > 0:
        col2.metric("Total Gasto Mês Atual", f"R$ {gastos_por_mes[0][1]:.2f}")
    else:
        col2.metric("Total Gasto Mês Atual", "R$ 0.00")

    if tipo_mais_gasto:
        col3.metric(f"Tipo Mais Gasto: {tipo_mais_gasto[0]}", f"R$ {tipo_mais_gasto[1]:.2f}")
    else:
        col3.metric("Tipo Mais Gasto", "Nenhum dado")

    # Gráficos
    st.markdown("---")
    st.write("### Gráficos Financeiros")
    registros = listar_registros_financeiros()

    if registros:
        df_financeiro = pd.DataFrame(registros, columns=["ID", "ID Processo", "Tipo", "Valor", "Data", "Descrição"])
        df_financeiro['Data'] = pd.to_datetime(df_financeiro['Data'])
        
        # Gráfico de Linhas (Gastos Diários no Mês)
        st.write("#### Gastos Diários no Mês")
        df_diario = df_financeiro.groupby(df_financeiro['Data'].dt.date)['Valor'].sum().reset_index()
        fig_line = px.line(df_diario, x="Data", y="Valor", title="Gastos Diários no Mês")
        st.plotly_chart(fig_line)

        # Gráfico de Histograma 
        st.write("#### Distribuição por Tipo")
        fig_hist = px.histogram(
            df_financeiro, 
            x="Tipo", 
            y="Valor", 
            color="Tipo",  # Diferentes cores para cada tipo de gasto
            title="Distribuição de Valores por Tipo", 
            histfunc="sum", 
            text_auto=True
        )
        st.plotly_chart(fig_hist)