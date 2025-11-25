#!/usr/bin/env python
# coding: utf-8

# In[1]:


import sqlite3

# 1. Abrir conexão com o banco
conn = sqlite3.connect("pizzaria.db")
cursor = conn.cursor()

# 2. Apagar todos os produtos (se quiser recriar do zero)
cursor.execute("DELETE FROM Produtos")

# 3. Inserir novamente os produtos
cursor.executemany("""
INSERT INTO Produtos (nome, preco, imagem) VALUES (?, ?, ?)
""", [
    ("Margherita", 29.90, "margherita.png"),
    ("Calabresa", 34.90, "calabresa.png"),
    ("Quatro Queijos", 39.90, "quatroqueijos.png")
])

# 4. Salvar alterações
conn.commit()

# 5. Fechar conexão
conn.close()

print("Produtos recriados com sucesso!")


# In[ ]:





# In[ ]:




