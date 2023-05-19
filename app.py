from flask import Flask, render_template, request, redirect
import pyodbc


app = Flask(__name__)


#CONEXIÓN CON LA BASE DE DATOS
def connection():
    s = 'LAPTOP-3H729AV9\SQLEXPRESS'    #Nombre del servidor
    d = 'E_CONDOSA'  #DataBase, va igual
    u = ''      #usuario de la BD
    p = ''      #contraseña de la BD
    #línea de conexión con autentificación de windows
    cstr = 'DRIVER={ODBC Driver 17 for SQL Server}; SERVER='+s+';DATABASE='+d+';Trusted_Connection=yes;'
    #línea de conexión con usuario de sql server
    #cstr = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER='+s+';DATABASE='+d+';UID='+u+';PWD='+ p
    conn = pyodbc.connect(cstr)
    return conn


#PÁGINA PRINCIPAL
@app.route("/")
def main():
    costos = []
    clientes = []
    conn = connection()
    cursor = conn.cursor()
    cursor.execute("select M.descripcion, P.nombre, M.totalCosto from MANTENIMIENTO M, PROVEEDOR P where P.idProveedor=M.idProveedor;")
    for row in cursor.fetchall():
        costos.append({"descripcion":row[0], "nombre":row[1], "totalCosto":row[2]})
    cursor.execute("select idCliente, nombre+' '+aPaterno+' '+aMaterno as nombreCompleto from CLIENTE;")
    for row in cursor.fetchall():
        clientes.append({"idCliente":row[0], "nombreCompleto":row[1]})
    conn.close()
    return render_template("index.html", costos = costos, clientes = clientes)

@app.route('/calculado')
def calculado():
    montos = []
    costos = []
    clientes = []
    conn = connection()
    cursor = conn.cursor()
    cursor.execute("select M.descripcion, P.nombre, M.totalCosto from MANTENIMIENTO M, PROVEEDOR P where P.idProveedor=M.idProveedor;")
    for row in cursor.fetchall():
        costos.append({"descripcion":row[0], "nombre":row[1], "totalCosto":row[2]})
    cursor.execute("select idCliente, nombre+' '+aPaterno+' '+aMaterno as nombreCompleto from CLIENTE;")
    for row in cursor.fetchall():
        clientes.append({"idCliente":row[0], "nombreCompleto":row[1]})
    cursor.execute("select CAST(((sum(M.totalCosto)/count(CL.idCliente))*0.5) AS DECIMAL(20,2)) as minimo, 10000.00 as caja from MANTENIMIENTO M, CLIENTE CL;")
    for row in cursor.fetchall():
        montos.append({"monto":row[0], "caja":row[1]})
    conn.close()
    return render_template("index.html", costos = costos, clientes = clientes, montos = montos)

@app.route('/recibo/<int:id>')
def recibo(id):
    datos = []
    recibos = []
    detalles = []
    resumenes = []
    conn = connection()
    cursor = conn.cursor()
    cursor.execute("select top (1) C.nombre+' '+C.aPaterno+' '+C.aMaterno as nombreCompleto,"+
                   " DO.direccion,C.nroDNI,R.fechaEmision,R.fechaVencimiento from CLIENTE C,"+
                   " CASA_DEPARTAMENTO DO, RECIBO R where C.idCliente="+str(id)+" AND DO.idCliente="+str(id)+
                   " AND R.idDomicilio = DO.idDomicilio;")
    for row in cursor.fetchall():
        datos.append({"nombreCompleto":row[0], "direccion":row[1], "nroDNI":row[2], "fechaEmision":row[3], "fechaVencimiento":row[4]})

    cursor.execute("select top (1) R.idRecibo, DO.area from CASA_DEPARTAMENTO DO, RECIBO R"+
                   " where DO.idCliente = "+str(id)+" AND R.idDomicilio=DO.idDomicilio;")
    for row in cursor.fetchall():
        recibos.append({"idRecibo":row[0], "area":row[1]})

    cursor.execute("select R.idRecibo as recibo, M.descripcion, P.nombre,"+
                   " CAST(R.montoMantenimiento AS DECIMAL(20,2)) as monto from RECIBO R,"+
                   " MANTENIMIENTO M, PROVEEDOR P where R.idDomicilio = (select idDomicilio"+
                   " from CASA_DEPARTAMENTO where idCliente="+str(id)+") AND "+
                   "M.idMantenimiento=R.idMantenimiento AND P.idProveedor=(select"+
                   " idProveedor from MANTENIMIENTO where idMantenimiento=(select"+
                   " idMantenimiento=R.idMantenimiento));")
    for row in cursor.fetchall():
        detalles.append({"recibo":row[0], "descripcion":row[1], "nombre":row[2], "monto":row[3]})

    cursor.execute("select CAST(sum(R.montoMantenimiento) AS DECIMAL(20,2)) as neto, CAST((sum(R.montoMantenimiento)*0.18)"+
                   " AS DECIMAL(20,2)) as igv, CAST((sum(R.montoMantenimiento)*1.18) AS DECIMAL(20,2)) as total from RECIBO"+
                   " R where R.idDomicilio = (select idDomicilio from CASA_DEPARTAMENTO where idCliente="+str(id)+");")
    for row in cursor.fetchall():
        resumenes.append({"neto":row[0], "igv":row[1], "total":row[2]})

    conn.close()
    return render_template("recibo.html", datos = datos, recibos = recibos, detalles = detalles, resumenes = resumenes)


#INICIA LA APP
if(__name__=="__main__"):
    app.run(debug=True, port=5000)