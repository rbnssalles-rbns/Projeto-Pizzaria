#!/usr/bin/env python
# coding: utf-8

# In[1]:


#Parte 1 — Setup e Funções
import streamlit as st
import sqlite3

# ---------------- Configuração inicial ----------------
# Número do WhatsApp (com DDI 55 + DDD + número, sem símbolos)
WHATSAPP_NUMBER = "5585985417565"  # Exemplo. Troque pelo número oficial da pizzaria.
WHATSAPP_LINK_BASE = f"https://wa.me/{WHATSAPP_NUMBER}"

# ---------------- Funções de banco ----------------
def cadastrar_cliente(nome, endereco, telefone):
    """Cadastra um novo cliente no banco SQLite."""
    conn = sqlite3.connect("pizzaria.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO Clientes (nome, endereco, telefone) VALUES (?, ?, ?)",
            (nome, endereco, telefone),
        )
        conn.commit()
        return f"Cliente '{nome}' cadastrado com sucesso!"
    except sqlite3.IntegrityError:
        return f"Já existe um cliente com o telefone {telefone}."
    finally:
        conn.close()

def buscar_cliente_por_telefone(telefone):
    """Busca cliente pelo telefone (retorna id e nome)."""
    conn = sqlite3.connect("pizzaria.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome FROM Clientes WHERE telefone = ?", (telefone,))
    resultado = cursor.fetchone()
    conn.close()
    return (resultado[0], resultado[1]) if resultado else (None, None)

def listar_produtos():
    """Lista todos os produtos cadastrados no banco."""
    conn = sqlite3.connect("pizzaria.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, preco, imagem FROM Produtos")
    produtos = cursor.fetchall()
    conn.close()
    return produtos

def registrar_pedido(cliente_id, produto_id, forma_pagamento):
    """Registra um pedido no banco."""
    conn = sqlite3.connect("pizzaria.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Pedidos (cliente_id, produto_id, forma_pagamento) VALUES (?, ?, ?)",
        (cliente_id, produto_id, forma_pagamento),
    )
    conn.commit()
    conn.close()
    
#Parte 2 — Interface Streamlit
# ---------------- Interface Streamlit ----------------
import re  # necessário para limpar o telefone

st.set_page_config(page_title="Pizzaria Rubens", layout="wide")
st.title("🍕 Pizzaria Rubens")

# Menu lateral
menu = st.sidebar.radio("Menu", ["Início", "Cadastro", "Cardápio", "Finalizar Pedido", "Meus pedidos"])

# Sessão carrinho e dados do cliente
if "carrinho" not in st.session_state:
    st.session_state["carrinho"] = []
if "telefone" not in st.session_state:
    st.session_state["telefone"] = None
if "cliente_id" not in st.session_state:
    st.session_state["cliente_id"] = None

# ---------------- Páginas ----------------
if menu == "Início":
    st.subheader("Bem-vindo à Pizzaria Rubens!")
    st.write("Escolha uma opção no menu lateral.")
    st.link_button("📞 Falar pelo WhatsApp", f"{WHATSAPP_LINK_BASE}?text=Olá,%20quero%20fazer%20um%20pedido")

elif menu == "Cadastro":
    st.subheader("Cadastro de Cliente")
    nome = st.text_input("Nome")
    endereco = st.text_input("Endereço")
    telefone = st.text_input("Telefone (11 dígitos)")
    
    if st.button("Cadastrar"):
        telefone_limpo = re.sub(r"\D", "", telefone)  # Remove tudo que não for número
        if len(telefone_limpo) == 11:
            msg = cadastrar_cliente(nome, endereco, telefone_limpo)
            st.success(msg)
            st.session_state["telefone"] = telefone_limpo
        else:
            st.error("Telefone inválido. Use 11 dígitos, ex: 85985417565")

elif menu == "Cardápio":
    st.subheader("Cardápio")
    telefone = st.text_input("Informe seu telefone (11 dígitos)", value=st.session_state["telefone"] or "")
    telefone_limpo = re.sub(r"\D", "", telefone)
    if telefone_limpo:
        cliente_id, cliente_nome = buscar_cliente_por_telefone(telefone_limpo)
        if cliente_id:
            st.session_state["telefone"] = telefone_limpo
            st.session_state["cliente_id"] = cliente_id
            st.write(f"Cliente: {cliente_nome} ({telefone_limpo})")

            produtos = listar_produtos()
            for idp, nome, preco, imagem in produtos:
                col1, col2 = st.columns([1, 2])
                with col1:
                    if imagem:
                        st.image(f"static/{imagem}", width=120)
                with col2:
                    st.write(f"**{nome}** - R$ {preco:.2f}")
                    if st.button(f"Adicionar {nome}", key=f"add_{idp}"):
                        st.session_state["carrinho"].append(idp)
                    if st.button(f"Remover {nome}", key=f"rem_{idp}"):
                        if idp in st.session_state["carrinho"]:
                            st.session_state["carrinho"].remove(idp)

            # Mostrar carrinho
            if st.session_state["carrinho"]:
                st.subheader("🛒 Seu carrinho")
                produtos = listar_produtos()
                mapa = {p[0]: p for p in produtos}
                total = 0
                for pid in st.session_state["carrinho"]:
                    _, nome, preco, _ = mapa[pid]
                    st.write(f"- {nome} | R$ {preco:.2f}")
                    total += preco
                st.write(f"**Total: R$ {total:.2f}**")
                st.link_button("Finalizar pedido", "#Finalizar Pedido")
        else:
            st.warning("Telefone não encontrado. Faça o cadastro primeiro.")

elif menu == "Finalizar Pedido":
    st.subheader("Finalizar Pedido")
    if not st.session_state["carrinho"]:
        st.info("Seu carrinho está vazio.")
    else:
        forma = st.selectbox("Forma de pagamento", ["Dinheiro", "Pix", "Crédito", "Débito"])
        if st.button("Confirmar Pedido"):
            for produto_id in st.session_state["carrinho"]:
                registrar_pedido(st.session_state["cliente_id"], produto_id, forma)
            st.session_state["carrinho"] = []
            if forma == "Pix":
                st.success("Pedido finalizado com sucesso! Pagamento via Pix.")
                qr_src = "https://api.qrserver.com/v1/create-qr-code/?data=chavepixficticia123&size=180x180"
                st.image(qr_src, caption="QR Code Pix")
                st.write("Chave Pix: **chavepixficticia123**")
            else:
                st.success(f"Pedido finalizado com sucesso! Pagamento via {forma}.")
            st.link_button("📦 Acompanhar pedido no WhatsApp", f"{WHATSAPP_LINK_BASE}?text=Olá,%20quero%20acompanhar%20meu%20pedido")

elif menu == "Meus pedidos":
    st.subheader("Meus pedidos")
    telefone = st.text_input("Informe seu telefone", value=st.session_state["telefone"] or "")
    telefone_limpo = re.sub(r"\D", "", telefone)
    if telefone_limpo:
        cliente_id, cliente_nome = buscar_cliente_por_telefone(telefone_limpo)
        if cliente_id:
            conn = sqlite3.connect("pizzaria.db")
            cursor = conn.cursor()
            cursor.execute("""
                SELECT Pedidos.id, Produtos.nome, Produtos.preco, Pedidos.forma_pagamento, Pedidos.status
                FROM Pedidos
                JOIN Produtos ON Pedidos.produto_id = Produtos.id
                WHERE Pedidos.cliente_id = ?
                ORDER BY Pedidos.id DESC
            """, (cliente_id,))
            pedidos = cursor.fetchall()
            conn.close()
            if pedidos:
                for pid, nome, preco, forma, status in pedidos:
                    st.write(f"Pedido #{pid} | {nome} - R$ {preco:.2f} | {forma} | Status: {status}")
            else:
                st.info("Você ainda não tem pedidos.")
        else:
            st.warning("Telefone não encontrado.")


# In[ ]:




