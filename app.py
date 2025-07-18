
import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="Painel de Bônus - LOG | 2º Trimestre", layout="wide")

df = pd.read_json("colaboradores_bonus_log_2tri.json")
with open("indicadores_nao_entregues_atualizado.json", "r", encoding="utf-8") as f:
    indicadores_perdidos = json.load(f)
with open("vistoriadores_erros_por_mes.json", "r", encoding="utf-8") as f:
    erros_por_vistoriador = json.load(f)

st.title("🚀 Painel de Bônus - LOG | 2º Trimestre")

col1, col2, col3, col4 = st.columns(4)
with col1:
    filtro_nome = st.text_input("🔍 Buscar por nome, função ou cidade")
with col2:
    empresas = ["Todas"] + sorted(df["EMPRESA"].unique())
    filtro_empresa = st.selectbox("🏢 Filtrar por empresa", empresas)
with col3:
    funcoes = ["Todas"] + sorted(df["FUNÇÃO"].unique())
    filtro_funcao = st.selectbox("👤 Filtrar por função", funcoes)
with col4:
    cidades = ["Todas"] + sorted(df["CIDADE"].unique())
    filtro_cidade = st.selectbox("📍 Filtrar por cidade", cidades)

meses = ["Trimestre", "ABRIL", "MAIO", "JUNHO"]
filtro_mes = st.radio("📅 Visualizar por mês:", meses, horizontal=True)

dados = df.copy()
if filtro_nome:
    dados = dados[dados["NOME"].str.contains(filtro_nome, case=False, na=False)]
if filtro_empresa != "Todas":
    dados = dados[dados["EMPRESA"] == filtro_empresa]
if filtro_funcao != "Todas":
    dados = dados[dados["FUNÇÃO"] == filtro_funcao]
if filtro_cidade != "Todas":
    dados = dados[dados["CIDADE"] == filtro_cidade]

if filtro_mes == "Trimestre":
    dados_agrupado = dados.groupby("NOME").agg({
        "EMPRESA": "first",
        "CIDADE": "first",
        "FUNÇÃO": "first",
        "VALOR MENSAL": "sum",
        "VALOR RECEBIDO": "sum",
        "VALOR PERDIDO": "sum",
        "% CUMPRIDO": "mean",
        "DESTAQUE": "first"
    }).reset_index()
else:
    dados_agrupado = dados[dados["MÊS"].str.upper() == filtro_mes.upper()]

st.markdown("### 📊 Resumo Geral")
total = dados_agrupado["VALOR MENSAL"].sum()
real = dados_agrupado["VALOR RECEBIDO"].sum()
perdido = dados_agrupado["VALOR PERDIDO"].sum()
st.success(f"💰 **Total possível:** R$ {total:,.2f}")
st.info(f"📈 **Recebido:** R$ {real:,.2f}")
st.error(f"📉 **Deixou de ganhar:** R$ {perdido:,.2f}")

if filtro_mes != "Trimestre" and filtro_empresa != "Todas":
    resumo_mes = indicadores_perdidos.get(filtro_empresa, {}).get("resumo", {}).get(filtro_mes.upper(), [])
    if resumo_mes:
        st.warning("⚠️ **Indicadores não cumpridos pela EMPRESA no mês de " + filtro_mes.upper() + ":** " + ", ".join(resumo_mes))

st.markdown("### 👥 Colaboradores")
cols = st.columns(3)

for idx, row in dados_agrupado.iterrows():
    nome_colab = row["NOME"]
    nome_upper = str(nome_colab).upper()
    cor_destaque = "#d4edda" if row["DESTAQUE"] == "melhor" else "#f8d7da" if row["DESTAQUE"] == "pior" else "#f9f9f9"

    indicadores_colab = []
    if filtro_mes != "Trimestre" and filtro_empresa != "Todas":
        colabs = indicadores_perdidos.get(filtro_empresa, {}).get("colaboradores", {}).get(filtro_mes.upper(), {})
        if nome_upper in colabs:
            indicadores_colab.extend(colabs[nome_upper])
        erros_mes = erros_por_vistoriador.get(filtro_mes.upper(), {})
        if nome_upper in erros_mes:
            qtd_erros = erros_mes[nome_upper]
            if qtd_erros >= 6 and "Erros de Vistoria" not in indicadores_colab:
                indicadores_colab.append("Erros de Vistoria")

    with cols[idx % 3]:
        meta_fmt = f"R$ {row['VALOR MENSAL']:,.2f}"
        recebido_fmt = f"R$ {row['VALOR RECEBIDO']:,.2f}"
        perdido_fmt = f"R$ {row['VALOR PERDIDO']:,.2f}"
        cumprimento_fmt = f"{row['% CUMPRIDO']:.1f}"
        tipo_meta = "Mensal" if filtro_mes != "Trimestre" else "Trimestral"

        html = f'''
        <div style="border:1px solid #ccc;padding:16px;border-radius:12px;margin-bottom:12px;background:{cor_destaque}">
            <h4>{nome_colab.title()}</h4>
            <p><strong>{row["FUNÇÃO"]}</strong> - {row["CIDADE"]}</p>
            <p><strong>Meta {tipo_meta}:</strong> {meta_fmt}<br>
            <strong>Recebido:</strong> {recebido_fmt}<br>
            <strong>Deixou de ganhar:</strong> {perdido_fmt}<br>
            <strong>Cumprimento:</strong> {cumprimento_fmt}%</p>
            <div style="height: 10px; background: #eee; border-radius: 5px; overflow: hidden;">
                <div style="width: {cumprimento_fmt}%; background: black; height: 100%;"></div>
            </div>
        </div>
        '''
        st.markdown(html, unsafe_allow_html=True)

        if indicadores_colab:
            st.markdown("🚫 **Indicadores Perdidos:**")
            for indicador in indicadores_colab:
                if indicador == "Erros de Vistoria":
                    qtd = erros_por_vistoriador.get(filtro_mes.upper(), {}).get(nome_upper, None)
                    if qtd is not None:
                        st.markdown(f"- {indicador} ({qtd} erros)")
                    else:
                        st.markdown(f"- {indicador}")
                else:
                    st.markdown(f"- {indicador}")
