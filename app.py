from flask import Flask, request, json, render_template, url_for, session, flash, redirect

from flask_bcrypt import Bcrypt

import mysql.connector

import sys

app = Flask(__name__)
app.config['SECRET_KEY'] = 'abc'
bcrypt = Bcrypt()


def getDB():
    try:
        db_conexao = mysql.connector.connect(
            host='mysql-352ac4ff-hos1r1s-5fad.a.aivencloud.com',
            port='27307',
            user='avnadmin',
            password='AVNS_PF9iTXRQUVHotQVEs75',
            database='defaultdb',
        )
        return db_conexao
    
    except mysql.connector.Error as erro:
        print(f'Erro connection com o BANCO DE DADOS: {erro}')
        sys.exit(1)




@app.route('/')
def index():
    return render_template('home.html')

@app.route('/alerta')
def alerta():
    return render_template('alerta.html')

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        user_login = request.form.get('Login')
        user_password = request.form.get('Senha')
    
        conexao = getDB()
        cursor = conexao.cursor(dictionary=True)
        
        cursor.execute(f"SELECT * FROM Usuarios WHERE login = '{user_login}'")
        usuario = cursor.fetchone()

        conexao.close()

        if usuario:
            
            #verifica se a senha é igual a encriptada pelo banco.
            if bcrypt.check_password_hash(usuario['Senha'], user_password) and usuario['Funcao'] == 'Admin':
            
                session['IDUsuario'] = usuario['ID']
                session['Login'] = usuario['Login']
                session['Permissao'] = usuario['Funcao']

                return redirect(url_for('itens'))

            elif bcrypt.check_password_hash(usuario['Senha'], user_password) and usuario['Funcao'] == 'Chefe':
            
                session['IDUsuario'] = usuario['ID']
                session['Login'] = usuario['Login']
                session['Permissao'] = usuario['Funcao']

                return redirect(url_for('itens')), 200
            
            elif bcrypt.check_password_hash(usuario['Senha'], user_password) and usuario['Funcao'] == 'Usuario':
            
                session['IDUsuario'] = usuario['ID']
                session['Login'] = usuario['Login']
                session['Permissao'] = usuario['Funcao']

                return redirect(url_for('itens')), 200

            else:
                flash('Senha incorreta!', 'danger')

        else:
            flash('Email incorreto!', 'danger')
        
    return render_template('login.html')






@app.route('/itens', methods=['GET', 'POST'])
def itens():
    conexao = getDB()
    cursor = conexao.cursor()

    pesquisa = request.form.get('Pesquisa')
    permissao = session.get('Permissao')
    
    if request.method == 'POST':

        cursor.execute("SELECT IDItem, Tipo, IDLivro, IDMaterial, StatusItem FROM Item")
        itens = []
        
        for row in cursor:
            IDItem, Tipo, IDLivro, IDMaterial, StatusItem = row
            itens.append({
                "IDItem": IDItem,
                "Tipo": Tipo,
                "IDLivro": IDLivro,
                "IDMaterial": IDMaterial,
                "StatusItem": StatusItem
            })

        resultados_consulta = []

        for item in itens:

                conexao = getDB()
                cursor = conexao.cursor()

                if item['Tipo'] == 'Livro':
                    chave = item['IDLivro']
                    cursor.execute('SELECT * FROM Livros WHERE IDLivro LIKE "{0}" OR Titulo LIKE "{0}" OR Autor LIKE "{0}" OR Categoria LIKE "{0}" OR EstadoConservacao LIKE "{0}" OR LocalizacaoFisica LIKE "{0}"'.format('%' + pesquisa + '%'))
                    

                
                elif item['Tipo'] == 'Material':
                    chave = item['IDMaterial']
                    cursor.execute('SELECT * FROM MateriaisDidaticos WHERE IDMaterial LIKE "{0}" OR Descricao LIKE "{0}" OR NumeroSerie LIKE "{0}" OR Categoria LIKE "{0}" OR EstadoConservacao LIKE "{0}" OR LocalizacaoFisica LIKE "{0}"'.format('%' + pesquisa + '%'))

                for row in cursor:
                    if row not in resultados_consulta:
                        resultados_consulta.append(row)

                tamanho = len(resultados_consulta)

        return render_template('itens.html', itens=itens, resultados_consulta = resultados_consulta, tamanho=tamanho, permissao=permissao)




    cursor.execute("SELECT IDItem, Tipo, IDLivro, IDMaterial, StatusItem FROM Item")
    itens = []
    
    for row in cursor:
        IDItem, Tipo, IDLivro, IDMaterial, StatusItem = row
        itens.append({
            "IDItem": IDItem,
            "Tipo": Tipo,
            "IDLivro": IDLivro,
            "IDMaterial": IDMaterial,
            "StatusItem": StatusItem
        })

    resultados_consulta = []

    for item in itens:

            conexao = getDB()
            cursor = conexao.cursor()

            if item['Tipo'] == 'Livro':
                chave = item['IDLivro']
                cursor.execute('SELECT * FROM Livros WHERE IDLivro = {0}'.format(chave))
                

            
            elif item['Tipo'] == 'Material':
                chave = item['IDMaterial']
                cursor.execute('SELECT * FROM MateriaisDidaticos WHERE IDMaterial = {0}'.format(chave))

            for row in cursor:
                resultados_consulta.append(row)

            tamanho = len(itens)

    return render_template('itens.html', itens=itens, resultados_consulta = resultados_consulta, tamanho=tamanho, permissao=permissao)










@app.route('/consulta/<IDItem>', methods=['GET', 'POST'])
def consulta(IDItem):

    conexao = getDB()
    cursor = conexao.cursor()
    IDUsuario = session.get('IDUsuario')
    permissao = session.get('Permissao')

    # METODO POST --------------------------------------------------------------------------

    if request.method == 'POST':
        
        conexao = getDB()
        cursor = conexao.cursor()

        status = "SELECT StatusItem FROM Item WHERE IDItem = {0}".format(IDItem)
        cursor.execute(status)
        status_item = cursor.fetchone()

        if permissao == 'Admin' or permissao == 'Chefe':

            if status_item[0] == "Disponivel":
                
                consulta_data = "SELECT CURDATE()"
                cursor.execute(consulta_data)
                data_emprestimo = cursor.fetchall()

                nova_data = "SELECT ADDDATE('{0}', INTERVAL 31 DAY)".format(data_emprestimo[0][0])
                cursor.execute(nova_data)
                data_limite = cursor.fetchall()
                
                query = "INSERT INTO Emprestimos(IDUsuario, IDItem, DataEmprestimo, DataDevolucaoPrevista) VALUES(%s, %s, %s, %s)"
                cursor.execute(query, (IDUsuario, IDItem, data_emprestimo[0][0], data_limite[0][0]))

                mudar_status = "UPDATE Item SET StatusItem = 'Indisponivel' WHERE IDItem = {0}".format(IDItem)
                cursor.execute(mudar_status)

                conexao.commit()
                conexao.close()

                return redirect(url_for('itens'))
   
            else:

                exclude = "DELETE FROM Emprestimos WHERE IDItem = {0}".format(IDItem)
                cursor.execute(exclude)

                mudar_status = "UPDATE Item SET StatusItem = 'Disponivel' WHERE IDItem = {0}".format(IDItem)
                cursor.execute(mudar_status)

                conexao.commit()
                conexao.close()

                return redirect(url_for('itens'))

        else:
            if status_item[0] == "Disponivel":
                
                consulta_data = "SELECT CURDATE()"
                cursor.execute(consulta_data)
                data_emprestimo = cursor.fetchall()

                nova_data = "SELECT ADDDATE('{0}', INTERVAL 31 DAY)".format(data_emprestimo[0][0])
                cursor.execute(nova_data)
                data_limite = cursor.fetchall()
                
                query = "INSERT INTO Emprestimos(IDUsuario, IDItem, DataEmprestimo, DataDevolucaoPrevista) VALUES(%s, %s, %s, %s)"
                cursor.execute(query, (IDUsuario, IDItem, data_emprestimo[0][0], data_limite[0][0]))

                mudar_status = "UPDATE Item SET StatusItem = 'Indisponivel' WHERE IDItem = {0}".format(IDItem)
                cursor.execute(mudar_status)

                conexao.commit()
                conexao.close()

                return redirect(url_for('itens'))

    # RENDER DA PAGINA ------------------------------------------------------------------------


    session['IDitem'] = IDItem

    query = 'SELECT Tipo, IDLivro, IDMaterial, StatusItem FROM Item WHERE IDItem = {0}'.format(IDItem)
    cursor.execute(query)
    tipo_item = cursor.fetchone()

    if tipo_item[0] == 'Livro':
        cursor.execute('SELECT IDLivro, Titulo, Autor, Descricao, Categoria, EstadoConservacao, LocalizacaoFisica, URICapaLivro FROM Livros WHERE IDLivro = {0}'.format(tipo_item[1]))
        for row in cursor:
            IDLivro, Titulo, Autor, Descricao, Categoria, EstadoConservacao, LocalizacaoFisica, URICapaLivro = row
            item = {'ISBN:': IDLivro,
                    'Título:': Titulo,
                    'Autor:': Autor,
                    'Descrição:': Descricao,
                    'Categoria:': Categoria,
                    'Estado de Conservacao': EstadoConservacao,
                    'Localização Física': LocalizacaoFisica,
                    'URI': URICapaLivro
                    }

    elif tipo_item[0] == 'Material':
        cursor.execute('SELECT IDMaterial, Descricao, NumeroSerie, Categoria, EstadoConservacao, LocalizacaoFisica, URIFotoMaterial FROM MateriaisDidaticos WHERE IDMaterial = {0}'.format(tipo_item[2]))
        for row in cursor:
            IDMaterial, Descricao, NumeroSerie, Categoria, EstadoConservacao, LocalizacaoFisica, URIFotoMaterial = row
            item = {'ID Material': IDMaterial,
                    'Descrição': Descricao,
                    'Número de Série': NumeroSerie,
                    'Estado de Conservação': EstadoConservacao,
                    'Localização Física': LocalizacaoFisica,
                    'URI': URIFotoMaterial
                    }

    conexao.close()

    return render_template('consulta.html', item=item, status=tipo_item[3], permissao=permissao)










@app.route('/update/<IDItem>', methods=['GET', 'POST'])
def update(IDItem):

    conexao = getDB()
    cursor = conexao.cursor()
    permissao = session.get('Permissao')

    cursor.execute('SELECT IDItem, Tipo, IDLivro, IDMaterial FROM Item WHERE IDItem = {0}'.format(IDItem))
    atributos = cursor.fetchone()

    if request.method == 'POST':
        
        conexao = getDB()
        cursor = conexao.cursor()

        if atributos[1] == 'Livro':

            titulo = request.form.get('Titulo')
            autor = request.form.get('Autor')
            descricao = request.form.get('Descricao')
            categoria = request.form.get('Categoria')
            estado = request.form.get('Estado')
            localizacao = request.form.get('Localizacao')
            uri_capa = request.form.get('URI_Capa')

            query = """UPDATE Livros SET Titulo='{0}',
                                          Autor='{1}',
                                          Descricao='{2}',
                                          Categoria='{3}',
                                          EstadoConservacao='{4}',
                                          LocalizacaoFisica='{5}',
                                          URICapaLivro='{6}' 
                                          WHERE IDLivro = {7}""".format(titulo, autor, descricao, categoria, estado, localizacao, uri_capa, atributos[2])
            
            cursor.execute(query)

            conexao.commit()
            conexao.close()

            return redirect(url_for('itens'))
        
        elif atributos[1] == 'Material':

            descricao = request.form.get('Descricao')
            numero_serie = request.form.get('Numero_Serie')
            categoria = request.form.get('Categoria')
            estado = request.form.get('Estado')
            localizacao = request.form.get('Localizacao')
            uri_material = request.form.get('URI_Material')

            query = """UPDATE MateriaisDidaticos SET Descricao='{0}',
                                         NumeroSerie='{1}',
                                         Categoria='{2}',
                                         EstadoConservacao='{3}',
                                         LocalizacaoFisica='{4}',
                                         URIFotoMaterial='{5}' 
                                         WHERE IDMaterial = {6}""".format(descricao, numero_serie, categoria, estado, localizacao, uri_material, atributos[3])
            
            cursor.execute(query)

            conexao.commit()
            conexao.close()

            return redirect(url_for('itens'))

    # RENDER DA PAGINA ------------------------------------------------------------------------


    session['IDitem'] = IDItem

    query = 'SELECT Tipo, IDLivro, IDMaterial FROM Item WHERE IDItem = {0}'.format(IDItem)
    cursor.execute(query)
    tipo_item = cursor.fetchone()

    if tipo_item[0] == 'Livro':
        cursor.execute('SELECT IDLivro, Titulo, Autor, Descricao, Categoria, EstadoConservacao, LocalizacaoFisica, URICapaLivro FROM Livros WHERE IDLivro = {0}'.format(tipo_item[1]))

    elif tipo_item[0] == 'Material':
        cursor.execute('SELECT IDMaterial, Descricao, NumeroSerie, Categoria, EstadoConservacao, LocalizacaoFisica, URIFotoMaterial FROM MateriaisDidaticos WHERE IDMaterial = {0}'.format(tipo_item[2]))
        
    item = cursor.fetchone()

    conexao.close()

    lista_livro = ['Titulo', 'Autor', 'Descricao', 'Categoria', 'Estado', 'Localizacao', 'URI_Capa']
    lista_material = ['Descricao', 'Numero_Serie', 'Categoria', 'Estado', 'Localizacao', 'URI_Material']

    len_livro = len(lista_livro)
    len_material = len(lista_material)

    return render_template('update.html', item=item[1:], tipo=atributos[1], len_livro=len_livro, len_material=len_material, lista_livro=lista_livro, lista_material=lista_material, permissao=permissao)









@app.route('/delete/<IDItem>', methods=['GET', 'POST'])
def delete(IDItem):

    conexao = getDB()
    cursor = conexao.cursor()
    permissao = session.get('Permissao')

    cursor.execute('SELECT Tipo, IDLivro, IDMaterial FROM Item WHERE IDItem = {0}'.format(IDItem))
    atributos = cursor.fetchone()

    if request.method == 'POST':

        if atributos[0] == 'Livro':
            cursor.execute('DELETE FROM Item WHERE IDLivro = {0}'.format(atributos[1]))
            cursor.execute('DELETE FROM Livros WHERE IDLivro = {0}'.format(atributos[1]))

            conexao.commit()
            conexao.close()
            
            return redirect(url_for('itens'))

        elif atributos[0] == 'Material':
            cursor.execute('DELETE FROM Item WHERE IDMaterial = {0}'.format(atributos[2]))
            cursor.execute('DELETE FROM MateriaisDidaticos WHERE IDMaterial = {0}'.format(atributos[2]))

            conexao.commit()
            conexao.close()

            return redirect(url_for('itens'))
        
    # RENDER DA PAGINA ------------------------------------------------------------------------


    session['IDitem'] = IDItem

    query = 'SELECT Tipo, IDLivro, IDMaterial, StatusItem FROM Item WHERE IDItem = {0}'.format(IDItem)
    cursor.execute(query)
    tipo_item = cursor.fetchone()

    if tipo_item[0] == 'Livro':
        cursor.execute('SELECT IDLivro, Titulo, Autor, Descricao, Categoria, EstadoConservacao, LocalizacaoFisica, URICapaLivro FROM Livros WHERE IDLivro = {0}'.format(tipo_item[1]))
        for row in cursor:
            IDLivro, Titulo, Autor, Descricao, Categoria, EstadoConservacao, LocalizacaoFisica, URICapaLivro = row
            item = {'ISBN:': IDLivro,
                    'Título:': Titulo,
                    'Autor:': Autor,
                    'Descrição:': Descricao,
                    'Categoria:': Categoria,
                    'Estado de Conservacao': EstadoConservacao,
                    'Localização Física': LocalizacaoFisica,
                    'URI': URICapaLivro
                    }

    elif tipo_item[0] == 'Material':
        cursor.execute('SELECT IDMaterial, Descricao, NumeroSerie, Categoria, EstadoConservacao, LocalizacaoFisica, URIFotoMaterial FROM MateriaisDidaticos WHERE IDMaterial = {0}'.format(tipo_item[2]))
        for row in cursor:
            IDMaterial, Descricao, NumeroSerie, Categoria, EstadoConservacao, LocalizacaoFisica, URIFotoMaterial = row
            item = {'ID Material': IDMaterial,
                    'Descrição': Descricao,
                    'Número de Série': NumeroSerie,
                    'Estado de Conservação': EstadoConservacao,
                    'Localização Física': LocalizacaoFisica,
                    'URI': URIFotoMaterial
                    }

    conexao.close()

    return render_template('delete.html', item=item, status=tipo_item[3], permissao=permissao)





@app.route('/cadastrar_usuario', methods=['GET', 'POST'])
def cadastrar_usuario():

    conexao = getDB()
    cursor = conexao.cursor()
    permissao = session.get('Permissao')

    if request.method == 'POST':

        id_user = request.form.get('ID')
        nome = request.form.get('Nome')
        sobrenome = request.form.get('Sobrenome')
        funcao = request.form.get('Funcao')
        login = request.form.get('Login')
        senha = request.form.get('Senha')
        uri = request.form.get('URI')

        senha_crypt = bcrypt.generate_password_hash(senha).decode('utf-8')

        query = "INSERT INTO Usuarios(ID, Nome, Sobrenome, Funcao, Login, Senha, URIFotoUsuario) VALUES (%s, %s, %s, %s, %s, %s, %s)"

        cursor.execute(query, (id_user, nome, sobrenome, funcao, login, senha_crypt, uri))
        
        conexao.commit()
        conexao.close()

        return redirect(url_for('itens'))
    
    return render_template('cadastro_usuario.html', permissao=permissao)





@app.route('/cadastrar_livro', methods=['GET', 'POST'])
def cadastrar_livro():

    conexao = getDB()
    cursor = conexao.cursor()
    permissao = session.get('Permissao')

    if request.method == 'POST':

        id_livro = request.form.get('IDLivro')
        titulo = request.form.get('Titulo')
        autor = request.form.get('Autor')
        descricao = request.form.get('Descricao')
        categoria = request.form.get('Categoria')
        data = request.form.get('Data')
        estado = request.form.get('Estado')
        localizacao = request.form.get('Localizacao')
        uri = request.form.get('URI')

        query = "INSERT INTO Livros(IDLivro, Titulo, Autor, Descricao, Categoria, DataAquisicao, EstadoConservacao, LocalizacaoFisica, URICapaLivro) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)"

        cursor.execute(query,(id_livro, titulo, autor, descricao, categoria, data, estado, localizacao, uri))

        adicionarEmItem = "INSERT INTO Item(Tipo, IDLivro, StatusItem) VALUES (%s, %s, %s)"
        cursor.execute(adicionarEmItem,("Livro", id_livro, "Disponivel"))
        
        conexao.commit()
        conexao.close()

        return redirect(url_for('itens'))
    
    return render_template('cadastro_livros.html', permissao=permissao)






@app.route('/cadastrar_material', methods=['GET', 'POST'])
def cadastrar_material():

    conexao = getDB()
    cursor = conexao.cursor()
    permissao = session.get('Permissao')

    if request.method == 'POST':

        id_material = request.form.get('IDMaterial')
        descricao = request.form.get('Descricao')
        numero = request.form.get('Numero')
        categoria = request.form.get('Categoria')
        data = request.form.get('Data')
        estado = request.form.get('Estado')
        localizacao = request.form.get('Localizacao')
        uri = request.form.get('URI')

        query = "INSERT INTO MateriaisDidaticos(IDMaterial, Descricao, NumeroSerie, Categoria, DataAquisicao, EstadoConservacao, LocalizacaoFisica, URIFotoMaterial) VALUES(%s, %s, %s, %s, %s, %s, %s, %s)"

        cursor.execute(query,(id_material, descricao, numero, categoria, data, estado, localizacao, uri))

        adicionarEmItem = "INSERT INTO Item(Tipo, IDMaterial, StatusItem) VALUES (%s, %s, %s)"
        cursor.execute(adicionarEmItem,("Material", id_material, "Disponivel"))
        
        conexao.commit()
        conexao.close()

        return redirect(url_for('itens'))
    
    return render_template('cadastro_materiais.html', permissao=permissao)




@app.route('/consulta_usuario', methods=['GET'])
def consulta_usuario():
    conexao = getDB()
    cursor = conexao.cursor()
    permissao = session.get('Permissao')
    
    cursor.execute("SELECT ID, Funcao, Login FROM Usuarios")
    usuarios = []
    
    for row in cursor:
        IDUsuario, Funcao, Login = row
        usuarios.append({
            "IDUsuario": IDUsuario,
            "Funcao": Funcao,
            "Login": Login
        })

    return render_template('consulta_usuarios.html', usuarios=usuarios, permissao=permissao)





@app.route('/update_usuario/<IDUsuario>', methods=['GET', 'POST'])
def update_usuario(IDUsuario):

    conexao = getDB()
    cursor = conexao.cursor()
    permissao = session.get('Permissao')

    cursor.execute('SELECT ID, Nome, Sobrenome, Senha, URIFotoUsuario FROM Usuarios WHERE ID = {0}'.format(IDUsuario))
    atributos = cursor.fetchone()

    if request.method == 'POST':
        
        conexao = getDB()
        cursor = conexao.cursor()


        nome = request.form.get('Nome')
        sobrenome = request.form.get('Sobrenome')
        senha = request.form.get('Senha')
        uri = request.form.get('URI')

        senha_crypt = bcrypt.generate_password_hash(senha).decode('utf-8')

        query = """UPDATE Usuarios SET Nome='{0}',
                                       Sobrenome='{1}',
                                       Senha='{2}',
                                       URIFotoUsuario='{3}' 
                                       WHERE ID = {4}""".format(nome, sobrenome, senha_crypt, uri, atributos[0])
            
        cursor.execute(query)

        conexao.commit()
        conexao.close()

        return redirect(url_for('itens'))
        

    # RENDER DA PAGINA ------------------------------------------------------------------------


    session['IDUsuario'] = IDUsuario

    query = 'SELECT ID, Nome, Sobrenome, Funcao, Login, Senha, URIFotoUsuario FROM Usuarios WHERE ID = {0}'.format(IDUsuario)
    cursor.execute(query)
    

    for row in cursor:
        IDUser, Nome, Sobrenome, Funcao, Login, Senha, URIFotoUsuario = row
        user = {
            'IDUsuario': IDUser,
            'Nome': Nome,
            'Sobrenome': Sobrenome,
            'Funcao': Funcao,
            'Login': Login,
            'Senha': Senha,
            'URIFotoUsuario': URIFotoUsuario
        }
        

    conexao.close()


    return render_template('update_usuario.html', user=user, permissao=permissao)




@app.route('/delete_usuario/<IDUsuario>', methods=['GET', 'POST'])
def delete_usuario(IDUsuario):

    conexao = getDB()
    cursor = conexao.cursor()
    permissao = session.get('Permissao')

    cursor.execute('SELECT ID, Nome, Sobrenome, Funcao, Login, URIFotoUsuario FROM Usuarios WHERE ID = {0}'.format(IDUsuario))
    atributos = cursor.fetchone()

    if request.method == 'POST':

        cursor.execute('DELETE FROM Usuarios WHERE ID = {0}'.format(atributos[0]))

        conexao.commit()
        conexao.close()
            
        return redirect(url_for('itens'))
        
    # RENDER DA PAGINA ------------------------------------------------------------------------


    session['IDUsuario'] = IDUsuario

    query = 'SELECT ID, Nome, Sobrenome, Funcao, Login, URIFotoUsuario FROM Usuarios WHERE ID = {0}'.format(IDUsuario)
    cursor.execute(query)
    

    for row in cursor:
        IDUser, Nome, Sobrenome, Funcao, Login, URIFotoUsuario = row
        user = {
            'IDUsuario': IDUser,
            'Nome': Nome,
            'Sobrenome': Sobrenome,
            'Funcao': Funcao,
            'Login': Login,
            'URIFotoUsuario': URIFotoUsuario
        }
        

    conexao.close()


    return render_template('delete_usuario.html', user=user, permissao=permissao)





@app.route('/emprestimos', methods=['GET'])
def emprestimos():
    conexao = getDB()
    cursor = conexao.cursor()
    permissao = session.get('Permissao')
    
    IDUsuario = session.get('IDUsuario')

    cursor.execute("SELECT IDItem, DataEmprestimo, DataDevolucaoPrevista, StatusSituacao FROM Emprestimos WHERE IDUsuario = {0}".format(IDUsuario))
    emprestimos = []
    
    for row in cursor:
        IDItem, DataEmprestimo, DataDevolucaoPrevista, StatusSituacao = row
        emprestimos.append({
            "IDUsuario": IDUsuario,
            "IDItem": IDItem,
            "DataEmprestimo": DataEmprestimo,
            "DataDevolucaoPrevista": DataDevolucaoPrevista,
            "StatusSituacao": StatusSituacao
        })

    conexao.close()

    return render_template('emprestimos.html', emprestimos=emprestimos, permissao=permissao)




@app.route('/consulta_emprestimos/<IDItem>', methods=['GET', 'POST'])
def consulta_emprestimos(IDItem):

    conexao = getDB()
    cursor = conexao.cursor()
    IDUsuario = session.get('IDUsuario')
    permissao = session.get('Permissao')

    consulta_data_inicial = "SELECT DataEmprestimo FROM Emprestimos WHERE IDItem = {0}".format(IDItem)
    cursor.execute(consulta_data_inicial)
    data_inicial = cursor.fetchone()

    consulta_data_limite = "SELECT DataDevolucaoPrevista FROM Emprestimos WHERE IDItem = {0}".format(IDItem)
    cursor.execute(consulta_data_limite)
    data_limite = cursor.fetchone()

    consulta_diferenca = "SELECT DATEDIFF('{0}','{1}')".format(data_limite[0], data_inicial[0])
    cursor.execute(consulta_diferenca)
    diferenca = cursor.fetchone()
    diferenca = int(diferenca[0])

    # METODO POST --------------------------------------------------------------------------

    if request.method == 'POST':
        
        conexao = getDB()
        cursor = conexao.cursor()
            
        exclude = "DELETE FROM Emprestimos WHERE IDItem = {0}".format(IDItem)
        cursor.execute(exclude)

        mudar_status = "UPDATE Item SET StatusItem = 'Disponivel' WHERE IDItem = {0}".format(IDItem)
        cursor.execute(mudar_status)

        conexao.commit()
        conexao.close()

        return redirect(url_for('emprestimos'))

    # RENDER DA PAGINA ------------------------------------------------------------------------


    session['IDitem'] = IDItem

    query = 'SELECT Tipo, IDLivro, IDMaterial, StatusItem FROM Item WHERE IDItem = {0}'.format(IDItem)
    cursor.execute(query)
    tipo_item = cursor.fetchone()

    if tipo_item[0] == 'Livro':
        cursor.execute('SELECT IDLivro, Titulo, Autor, Descricao, Categoria, EstadoConservacao, LocalizacaoFisica, URICapaLivro FROM Livros WHERE IDLivro = {0}'.format(tipo_item[1]))
        for row in cursor:
            IDLivro, Titulo, Autor, Descricao, Categoria, EstadoConservacao, LocalizacaoFisica, URICapaLivro = row
            item = {'ID': IDLivro, 'Titulo': Titulo}

    elif tipo_item[0] == 'Material':
        cursor.execute('SELECT IDMaterial, Descricao, NumeroSerie, Categoria, EstadoConservacao, LocalizacaoFisica, URIFotoMaterial FROM MateriaisDidaticos WHERE IDMaterial = {0}'.format(tipo_item[2]))
        for row in cursor:
            IDMaterial, Descricao, NumeroSerie, Categoria, EstadoConservacao, LocalizacaoFisica, URIFotoMaterial = row
            item = {'ID': IDMaterial, 'Titulo': Descricao}

    cursor.execute('SELECT DataEmprestimo, DataDevolucaoPrevista, StatusSituacao FROM Emprestimos WHERE IDItem = {0}'.format(IDItem))
    for row in cursor:
        DataEmprestimo, DataDevolucaoPrevista, StatusSituacao = row
        emprestimo = {
                        'DataEmprestimo': DataEmprestimo,
                        'DataDevolucaoPrevista': DataDevolucaoPrevista,
                        'StatusSituacao': StatusSituacao
                      }  

    conexao.close()

    return render_template('consulta_emprestimos.html', item=item, emprestimo=emprestimo, diferenca=diferenca, permissao=permissao)







@app.route('/update_emprestimos/<IDItem>', methods=['GET', 'POST'])
def update_emprestimos(IDItem):

    conexao = getDB()
    cursor = conexao.cursor()
    IDUsuario = session.get('IDUsuario')
    permissao = session.get('Permissao')

    consulta_data_inicial = "SELECT DataEmprestimo FROM Emprestimos WHERE IDItem = {0}".format(IDItem)
    cursor.execute(consulta_data_inicial)
    data_inicial = cursor.fetchone()

    consulta_data_limite = "SELECT DataDevolucaoPrevista FROM Emprestimos WHERE IDItem = {0}".format(IDItem)
    cursor.execute(consulta_data_limite)
    data_limite = cursor.fetchone()

    consulta_diferenca = "SELECT DATEDIFF('{0}','{1}')".format(data_limite[0], data_inicial[0])
    cursor.execute(consulta_diferenca)
    diferenca = cursor.fetchone()
    diferenca = int(diferenca[0])

    # METODO POST --------------------------------------------------------------------------

    if request.method == 'POST':
        
        conexao = getDB()
        cursor = conexao.cursor()
            
        nova_data = "SELECT ADDDATE(CURDATE(), INTERVAL 31 DAY)"
        cursor.execute(nova_data)
        data_limite = cursor.fetchone()

        att_emprestimo = "UPDATE Emprestimos SET DataDevolucaoPrevista = '{0}' WHERE IDItem = {1}".format(data_limite[0], IDItem)
        cursor.execute(att_emprestimo)

        conexao.commit()
        conexao.close()

        return redirect(url_for('emprestimos'))

    # RENDER DA PAGINA ------------------------------------------------------------------------


    session['IDitem'] = IDItem

    query = 'SELECT Tipo, IDLivro, IDMaterial, StatusItem FROM Item WHERE IDItem = {0}'.format(IDItem)
    cursor.execute(query)
    tipo_item = cursor.fetchone()

    if tipo_item[0] == 'Livro':
        cursor.execute('SELECT IDLivro, Titulo, Autor, Descricao, Categoria, EstadoConservacao, LocalizacaoFisica, URICapaLivro FROM Livros WHERE IDLivro = {0}'.format(tipo_item[1]))
        for row in cursor:
            IDLivro, Titulo, Autor, Descricao, Categoria, EstadoConservacao, LocalizacaoFisica, URICapaLivro = row
            item = {'ID': IDLivro, 'Titulo': Titulo}

    elif tipo_item[0] == 'Material':
        cursor.execute('SELECT IDMaterial, Descricao, NumeroSerie, Categoria, EstadoConservacao, LocalizacaoFisica, URIFotoMaterial FROM MateriaisDidaticos WHERE IDMaterial = {0}'.format(tipo_item[2]))
        for row in cursor:
            IDMaterial, Descricao, NumeroSerie, Categoria, EstadoConservacao, LocalizacaoFisica, URIFotoMaterial = row
            item = {'ID': IDMaterial, 'Titulo': Descricao}

    cursor.execute('SELECT DataEmprestimo, DataDevolucaoPrevista, StatusSituacao FROM Emprestimos WHERE IDItem = {0}'.format(IDItem))
    for row in cursor:
        DataEmprestimo, DataDevolucaoPrevista, StatusSituacao = row
        emprestimo = {
                        'DataEmprestimo': DataEmprestimo,
                        'DataDevolucaoPrevista': DataDevolucaoPrevista,
                        'StatusSituacao': StatusSituacao
                      }  

    conexao.close()

    return render_template('update_emprestimos.html', item=item, emprestimo=emprestimo, diferenca=diferenca, permissao=permissao)


if __name__ == '__main__':
    app.run()
