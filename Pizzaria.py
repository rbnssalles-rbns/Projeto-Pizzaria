#!/usr/bin/env python
# coding: utf-8

# In[2]:


# Parte 1 — Setup e inicialização
import streamlit as st
import sqlite3

st.set_page_config(page_title="Pizzaria Rubens", layout="wide")
st.title("🍕 Pizzaria Rubens")

# ---------------- Inicialização do banco (fiel ao modelo) ----------------
def inicializar_banco():
    conn = sqlite3.connect("pizzaria.db")
    cursor = conn.cursor()

    # Clientes: sem exigir UNIQUE por padrão no modelo,
    # porém o modelo espera evitar duplicidade comportamental via fluxo.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        endereco TEXT NOT NULL,
        telefone TEXT
    )
    """)

    # Produtos: para o Bloco 2 funcionar (IntegrityError), precisamos UNIQUE em nome.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT UNIQUE NOT NULL,
        preco REAL NOT NULL,
        imagem TEXT
    )
    """)

    # Pedidos: status padrão 'Recebido', como no modelo.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER,
        produto_id INTEGER,
        forma_pagamento TEXT,
        status TEXT DEFAULT 'Recebido',
        FOREIGN KEY (cliente_id) REFERENCES Clientes(id),
        FOREIGN KEY (produto_id) REFERENCES Produtos(id)
    )
    """)

    conn.commit()
    conn.close()

inicializar_banco()

# ---------------- Funções de banco (fieis ao modelo) ----------------
def cadastrar_cliente(nome, endereco, telefone):
    conn = sqlite3.connect("pizzaria.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO Clientes (nome, endereco, telefone) VALUES (?, ?, ?)",
            (nome, endereco, telefone)
        )
        conn.commit()
        return f"Cliente '{nome}' cadastrado com sucesso!"
    except sqlite3.IntegrityError:
        # Só ocorrerá se no futuro adicionarmos UNIQUE; mantemos mensagem compatível com o modelo
        return f"Já existe um cliente com o telefone {telefone}. Nenhuma ação realizada."
    finally:
        conn.close()

def buscar_cliente_por_telefone(telefone):
    conn = sqlite3.connect("pizzaria.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome FROM Clientes WHERE telefone = ?", (telefone,))
    resultado = cursor.fetchone()
    conn.close()
    return (resultado[0], resultado[1]) if resultado else (None, None)

def listar_produtos():
    conn = sqlite3.connect("pizzaria.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, preco, imagem FROM Produtos")
    produtos = cursor.fetchall()
    conn.close()
    return produtos

def registrar_pedido(cliente_id, produto_id, forma_pagamento):
    conn = sqlite3.connect("pizzaria.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Pedidos (cliente_id, produto_id, forma_pagamento)
        VALUES (?, ?, ?)
    """, (cliente_id, produto_id, forma_pagamento))
    conn.commit()
    conn.close()

# ---------------- Bloco 2 — Inserção com proteção contra duplicação (modelo) ----------------
def adicionar_produto(nome, preco, imagem):
    conn = sqlite3.connect("pizzaria.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO Produtos (nome, preco, imagem) VALUES (?, ?, ?)", (nome, preco, imagem))
        conn.commit()
    except sqlite3.IntegrityError:
        # Com UNIQUE em nome, evita duplicação silenciosamente
        pass
    finally:
        conn.close()

# Popula apenas uma vez (não duplica graças ao UNIQUE + IntegrityError)
adicionar_produto("Pizza Margherita", 35.0, "margherita.png")
adicionar_produto("Pizza Calabresa", 40.0, "calabresa.png")
adicionar_produto("Hambúrguer Artesanal", 25.0, "burger.png")
adicionar_produto("Refrigerante Lata", 6.0, "refrigerante.png")

# ---------------- Sessão (fiel ao modelo: cliente e carrinho) ----------------
if "carrinho" not in st.session_state:
    st.session_state["carrinho"] = []
if "telefone" not in st.session_state:
    st.session_state["telefone"] = None
if "cliente_id" not in st.session_state:
    st.session_state["cliente_id"] = None
if "cliente_nome" not in st.session_state:
    st.session_state["cliente_nome"] = None

# ---------------- Menu lateral ----------------
menu = st.sidebar.radio("Menu", ["Início", "Cadastro", "Cardápio", "Finalizar Pedido", "Meus pedidos"])

# Parte 2 — Interface Streamlit (fluxo fiel ao Flask)
# Página inicial
if menu == "Início":
    st.subheader("Bem-vindo à Pizzaria Rubens!")
    st.write("Escolha uma opção no menu lateral.")
    st.write("Se você já é cliente, vá direto ao Cardápio. Se ainda não é, faça o Cadastro.")

# Cadastro (POST-like)
elif menu == "Cadastro":
    st.subheader("Cadastro de Cliente")
    nome = st.text_input("Nome")
    endereco = st.text_input("Endereço")
    telefone = st.text_input("Telefone com DDD, no formato livre (ex.: (85)999999999)")

    if st.button("Cadastrar"):
        if nome and endereco and telefone:
            msg = cadastrar_cliente(nome, endereco, telefone)
            st.success(msg)
            # Identifica automaticamente e carrega sessão
            cid, cnome = buscar_cliente_por_telefone(telefone)
            if cid:
                st.session_state["cliente_id"] = cid
                st.session_state["cliente_nome"] = cnome
                st.session_state["telefone"] = telefone
                st.info("Cadastro concluído. Você já está identificado e pode acessar o Cardápio.")
        else:
            st.error("Preencha todos os campos para cadastrar.")

# Cardápio (sempre visível; identifica automaticamente se já há sessão)
elif menu == "Cardápio":
    st.subheader("Cardápio")

    # Identificação automática do cliente (se já estiver na sessão)
    cliente_id = st.session_state.get("cliente_id")
    cliente_nome = st.session_state.get("cliente_nome")
    telefone = st.session_state.get("telefone")

    if cliente_id and cliente_nome:
        st.write(f"Cliente identificado: {cliente_nome} ({telefone})")
    else:
        st.info("Você ainda não está identificado. O cardápio está visível, mas será necessário se identificar para finalizar o pedido.")

    # Exibir produtos sempre
    produtos = listar_produtos()
    if not produtos:
        st.warning("Nenhum produto cadastrado no momento.")
    else:
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
            mapa = {p[0]: p for p in produtos}
            total = 0
            for pid in st.session_state["carrinho"]:
                _, nome, preco, _ = mapa[pid]
                st.write(f"- {nome} | R$ {preco:.2f}")
                total += preco
            st.write(f"**Total: R$ {total:.2f}**")
        else:
            st.info("Seu carrinho está vazio.")

# Finalizar Pedido (exige estar identificado, mas cardápio não exige)
elif menu == "Finalizar Pedido":
    st.subheader("Finalizar Pedido")

    if not st.session_state["carrinho"]:
        st.info("Seu carrinho está vazio.")
    elif not st.session_state["cliente_id"]:
        st.warning("Para finalizar, você precisa estar cadastrado e identificado. Vá em 'Cadastro' primeiro.")
    else:
        forma = st.selectbox("Forma de pagamento", ["Dinheiro", "Pix", "Crédito", "Débito"])
        if st.button("Confirmar Pedido"):
            for produto_id in st.session_state["carrinho"]:
                registrar_pedido(st.session_state["cliente_id"], produto_id, forma)
            st.session_state["carrinho"] = []
            if forma == "Pix":
                st.success("Pedido finalizado! Pagamento via Pix.")
                qr_src = "https://api.qrserver.com/v1/create-qr-code/?data=chavepixficticia123&size=180x180"
                st.image(qr_src, caption="QR Code Pix")
                st.write("Chave Pix: **chavepixficticia123**")
            elif forma in ["Crédito", "Débito"]:
                st.success(f"Pedido finalizado! Pagamento via {forma}.")
            else:
                st.success("Pedido finalizado! Pagamento em dinheiro.")

# Meus pedidos (fiel ao modelo: JOIN + status 'Recebido')
elif menu == "Meus pedidos":
    st.subheader("Meus pedidos")
    if not st.session_state["cliente_id"]:
        st.warning("Você precisa estar cadastrado para visualizar seus pedidos.")
    else:
        conn = sqlite3.connect("pizzaria.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT Pedidos.id, Produtos.nome, Produtos.preco, Pedidos.forma_pagamento, Pedidos.status
            FROM Pedidos
            JOIN Produtos ON Pedidos.produto_id = Produtos.id
            WHERE Pedidos.cliente_id = ?
            ORDER BY Pedidos.id DESC
        """, (st.session_state["cliente_id"],))
        pedidos = cursor.fetchall()
        conn.close()

        if pedidos:
            for pid, nome, preco, forma, status in pedidos:
                st.write(f"Pedido #{pid} | {nome} - R$ {preco:.2f} | {forma} | Status: {status}")
        else:
            st.info("Você ainda não tem pedidos.")


# In[ ]:




