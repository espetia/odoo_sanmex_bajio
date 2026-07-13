
from odoo import http
from odoo.http import content_disposition, dispatch_rpc, request, serialize_exception as _serialize_exception
db_monodb = http.db_monodb



class snmx_consulta(http.Controller):
    @http.route('/api/snmx/consulta', type='json', auth='user')
    def Snmx_Consulta(self, dbname=None, **kw):
        uid = None
        response = None
        if request.session.db:
            dbname = request.session.db
            uid = request.session.uid
        try:
            if request.jsonrequest['params']['args'][3] == "INSERT":
                consulta = request.jsonrequest['params']['args'][4]['consulta']
                request.cr.execute(consulta)
                response = "Registro insertado"
            if request.jsonrequest['params']['args'][3] == "SELECT":
                request.cr.execute(request.jsonrequest['params']['args'][4]['consulta'])
                response = request.cr.fetchall()
        except Exception as e:
            se = _serialize_exception(e)
            error = {
                'code': 200,
                'message': "Odoo Server Error",
                'data': se
            }
            response = error

        return response

        # # create transaction cursor
        # cr = db.cursor()
        # try:
        #     res = pool.execute_cr(cr, uid, obj, method, *args, **kw)
        #     cr.commit() # all good, we commit
        # except Exception:
        #     cr.rollback() # error, rollback everything atomically
        #     raise
        # finally:
        #     cr.close() # always close cursor opened manually
        # return res