# -*- encoding: utf-8 -*-
#

from odoo import api, fields, models, _, tools

import os
import sys
import time
import tempfile
import base64
import binascii
import logging
_logger = logging.getLogger(__name__)
import base64
from lxml import etree as ET
import hashlib
import os
import subprocess

### Fin Sello ####
KEY_TO_PEM_CMD = 'openssl pkcs8 -in %s -inform der -outform pem -out %s -passin file:%s'
CER_TO_PFX_CMD = 'openssl pkcs12 -export -out %s -inkey %s -in %s -passout pass:%s'

openssl_path = ''
xsltproc_path = ''
xmllint_path = ''
all_paths = tools.config["addons_path"].split(",")
for my_path in all_paths:
    if os.path.isdir(os.path.join(my_path, 'webservice', 'depends_app')):
        openssl_path = my_path and os.path.join(my_path, 'webservice', 'depends_app', u'openssl_win') or ''
        xsltproc_path = my_path and os.path.join(my_path, 'webservice', 'depends_app', u'xsltproc_win') or ''
        xmllint_path = my_path and os.path.join(my_path, 'webservice', 'depends_app', u'xmllint_win') or ''

def exec_command_pipe(*args):
    # Agregue esta funcion, ya que con la nueva funcion original, de tools no funciona
# TODO: Hacer separacion de argumentos, no por espacio, sino tambien por "
# ", como tipo csv, pero separator espace & delimiter "
    cmd = ' '.join(args)
    if os.name == "nt":
        cmd = cmd.replace(
            '"', '')  # provisionalmente, porque no funcionaba en win32
    return os.popen2(cmd, 'b')

if os.name == "nt":
    #app_xsltproc = 'xsltproc.exe'
    app_openssl = 'openssl.exe'
    #app_xmllint = 'xmllint.exe'
else:
    #app_xsltproc = 'xsltproc'
    app_openssl = 'openssl'
    #app_xmllint = 'xmllint'

app_openssl_fullpath = os.path.join(openssl_path, app_openssl)
if not os.path.isfile(app_openssl_fullpath):
    app_openssl_fullpath = tools.find_in_path(app_openssl)
    if not os.path.isfile(app_openssl_fullpath):
        app_openssl_fullpath = False
        _logger.warning('Install openssl "sudo apt-get install openssl" to use webservice module.')

"""app_xsltproc_fullpath = os.path.join(xsltproc_path, app_xsltproc) or False
try:
    if not os.path.isfile(app_xsltproc_fullpath):
        app_xsltproc_fullpath = tools.find_in_path(app_xsltproc) or False
        if not os.path.isfile(app_xsltproc_fullpath):
            app_xsltproc_fullpath = False
            _logger.warning('Install xsltproc "sudo apt-get install xsltproc" to use webservice module.')
except Exception:
    _logger.warning("Install xsltproc 'sudo apt-get install xsltproc' to use webservice module.")"""

"""app_xmllint_fullpath = os.path.join(xmllint_path, app_xmllint)
if not os.path.isfile( app_xmllint_fullpath ):
    app_xmllint_fullpath = tools.find_in_path( app_xmllint )
    if not app_xmllint_fullpath:
        app_xmllint_fullpath = False
        _logger.warning('Install xmllint "sudo apt-get install xmllint" to use webservice module.')"""

def library_openssl_xsltproc_xmllint():
    msj = ''
    app_openssl_fullpath = os.path.join(openssl_path, app_openssl)
    if not os.path.isfile(app_openssl_fullpath):
        app_openssl_fullpath = tools.find_in_path(app_openssl)
        if not os.path.isfile(app_openssl_fullpath):
            app_openssl_fullpath = False
            _logger.warning('Install openssl "sudo apt-get install openssl" to use webservice module.')
            msj += 'Install openssl "sudo apt-get install openssl" to use webservice module.'
    
    app_xsltproc_fullpath = os.path.join(xsltproc_path, app_xsltproc) or False
    if not os.path.isfile(app_xsltproc_fullpath):
        app_xsltproc_fullpath = tools.find_in_path(app_xsltproc) or False
        try:
            if not os.path.isfile(app_xsltproc_fullpath):
                app_xsltproc_fullpath = False
                _logger.warning("Install xsltproc 'sudo apt-get install xsltproc' to use webservice module.")
                msj =  "Install xsltproc 'sudo apt-get install xsltproc' to use webservice module."
        except Exception:
            _logger.warning("Install xsltproc 'sudo apt-get install xsltproc' to use webservice module.")
            msj +=  "Install xsltproc 'sudo apt-get install xsltproc' to use webservice module."

    """app_xmllint_fullpath = os.path.join(xmllint_path, app_xmllint)
    if not os.path.isfile( app_xmllint_fullpath ):
        app_xmllint_fullpath = tools.find_in_path( app_xmllint )
        if not app_xmllint_fullpath:
            app_xmllint_fullpath = False
            _logger.warning('Install xmllint "sudo apt-get install xmllint" to use webservice module.')
            msj += 'Install xmllint "sudo apt-get install xmllint" to use webservice module.'"""
    #return msj, app_xsltproc_fullpath, app_openssl_fullpath, app_xmllint_fullpath
    return msj, app_openssl_fullpath
        

class facturae_certificate_library(models.Model):
    _name = 'facturae.certificate.library'
    
    def convert_key_cer_to_pem(self, key, password):
        with tempfile.NamedTemporaryFile('wb', suffix='.key', prefix='mx_einvoice.') as key_file, \
             tempfile.NamedTemporaryFile('wb', suffix='.txt', prefix='mx_einvoice.') as pwd_file, \
             tempfile.NamedTemporaryFile('rb', suffix='.key', prefix='mx_einvoice.') as keypem_file:
            key_file.write(key)
            key_file.flush()
            pwd_file.write(password)
            pwd_file.flush()
            subprocess.call((KEY_TO_PEM_CMD % (key_file.name, keypem_file.name, pwd_file.name)).split())
            key_pem = keypem_file.read()
        return key_pem

    def convert_cer_to_pfx(self, cer_pem, key_pem, password):
       with tempfile.NamedTemporaryFile('wb', suffix='.cer_pem', prefix='mx_einvoice.') as cer_pem_file, \
            tempfile.NamedTemporaryFile('wb', suffix='.key_pem', prefix='mx_einvoice.') as key_pem_file, \
            tempfile.NamedTemporaryFile('rb', suffix='.pfx', prefix='mx_einvoice.') as pfx_file:
           cer_pem_file.write(cer_pem)
           cer_pem_file.flush()
           key_pem_file.write(key_pem)
           key_pem_file.flush()
           
           subprocess.call((CER_TO_PFX_CMD % (pfx_file.name, 
                                              key_pem_file.name, 
                                              cer_pem_file.name, 
                                              password)).split())
           pfx_pem = pfx_file.read()
       return pfx_pem

    def b64str_to_tempfile(self, b64_str=None, file_suffix=None, file_prefix=None):
        
        (fileno, fname) = tempfile.mkstemp(file_suffix, file_prefix)
        f = open(fname, 'wb')
        f.write(base64.decodestring(b64_str or ''))
        f.close()
        os.close(fileno)
        return fname

    def _read_file_attempts(self, file_obj, max_attempt=12, seconds_delay=0.5):
        """
        @param file_obj : Object with the path of the file, more el mode
            of the file to create (read, write, etc)
        @param max_attempt : Max number of attempt
        @param seconds_delay : Seconds valid of delay
        """
        fdata = False
        cont = 1
        while True:
            time.sleep(seconds_delay)
            try:
                fdata = file_obj.read()
            except:
                pass
            if fdata or max_attempt < cont:
                break
            cont += 1
        return fdata

    def _transform_der_to_pem(self, fname_der, fname_out, fname_password_der=None, type_der='cer'):
        """
        @param fname_der : File.cer configurated in the company
        @param fname_out : Information encrypted in Base_64from certificate
            that is send
        @param fname_password_der : File that contain the password configurated
            in this Certificate
        @param type_der : cer or key
        """
        if not app_openssl_fullpath:
            raise UserError(_("Error!"), _(
                "Failed to find in path '%s' app. This app is required for sign Mexican Electronic Invoice"%(app_openssl) ))
        cmd = ''
        result = ''
        if type_der == 'cer':
            cmd = '"%s" x509 -inform DER -outform PEM -in "%s" -pubkey -out "%s"' % (
                app_openssl_fullpath, fname_der, fname_out)
        elif type_der == 'key':
            cmd = '"%s" pkcs8 -inform DER -outform PEM -in "%s" -passin file:%s -out "%s"' % (
                app_openssl_fullpath, fname_der, fname_password_der, fname_out)
        if cmd:
            args = tuple(cmd.split(' '))
            # input, output = tools.exec_command_pipe(*args)
            input, output = exec_command_pipe(*args)
            result = self._read_file_attempts(open(fname_out, "r"))
            input.close()
            output.close()
        return result

    
    def _transform_pem_to_pfx(self, fname_cer_pem, fname_key_pem, fname_out, pfx_password):
        """
        @param fname_cer_pem : File.cer.pem configurated in the company
        @param fname_key_pem : File.key.pem configurated in the company
        @param fname_out : PFX file
        @param fname_password_der : File that contain the password configurated
            in this Certificate
        @param type_der : cer or key
        """
        if not app_openssl_fullpath:
            raise UserError(_("Error!"), _(
                "Failed to find in path '%s' app. This app is required for sign Mexican Electronic Invoice"%(app_openssl) ))
        cmd = ''
        result = ''
        cmd = '%s pkcs12 -export -out %s -inkey %s -in %s -passout pass:%s' % (
                app_openssl_fullpath, fname_out, fname_key_pem, fname_cer_pem, pfx_password)
        
        if cmd:
            args = tuple(cmd.split(' '))
            # input, output = tools.exec_command_pipe(*args)
            input, output = exec_command_pipe(*args)
            result = self._read_file_attempts(open(fname_out, "r"))
            input.close()
            output.close()
        return result  
    
    
    def _get_param_serial(self, fname, fname_out=None, type='DER'):
        """
        @param fname : File.PEM with the information of the certificate
        @param fname_out : File.xml that is send
        """
        result = self._get_params(fname, params=['serial'], fname_out=fname_out, type=type)
        result = result and result.replace('serial=', '').replace(
            '33', 'B').replace('3', '').replace('B', '3').replace(
            ' ', '').replace('\r', '').replace('\n', '').replace('\r\n', '') or ''
        return result

    

    def _get_param_dates(self, fname, fname_out=None, date_fmt_return='%Y-%m-%d %H:%M:%S', type='DER'):
        """
        @param fname : File.cer with the information of the certificate
        @params fname_out : Path and name of the file.txt with info encrypted
        @param date_fmt_return : Format of the date used
        @param type : Type of file
        """
        months = {'Jan':'01',
                  'Feb':'02',
                  'Mar':'03',
                  'Apr':'04',
                  'May':'05',
                  'Jun':'06',
                  'Jul':'07', 
                  'Aug':'08',
                  'Sep':'09',
                  'Oct':'10',
                  'Nov':'11',
                  'Dec':'12'}
        result_dict = self._get_params_dict(fname, params=['dates'], fname_out=fname_out, type=type)
        translate_key = {
            'notAfter': 'enddate',
            'notBefore': 'startdate',
        }
        result2 = {}
        if result_dict:
            date_fmt_src = "%b %d %H:%M:%S %Y GMT"
            for key in result_dict.keys():
                date = result_dict[key]
                dia = (date[:6][-2:]).replace(' ', '0')
                new_date = date[:-4][-4:] + '-' + months[date[:3]] + '-' + dia #date[:6][-2:]
                result2[translate_key[key]] = new_date
        return result2

    def _get_params_dict(self, fname, params=None, fname_out=None, type='DER'):
        """
        @param fname : File.cer with the information of the certificate
        @param params : List of params used for this function
        @param fname_out : Path and name of the file.txt with info encrypted
        @param type : Type of file
        """
        result = self._get_params(fname, params, fname_out, type)
        result = result.replace('\r\n', '\n').replace('\r', '\n')
        result = result.rstrip('\n').lstrip('\n').rstrip(' ').lstrip(' ')
        result_list = result.split('\n')
        params_dict = {}
        for result_item in result_list:
            if result_item:
                key, value = result_item.split('=')
                params_dict[key] = value
        return params_dict

    def _get_params(self, fname, params=None, fname_out=None, type='DER'):
        """
        @params: list [noout serial startdate enddate subject issuer dates]
        @type: str DER or PEM
        """
        #msj, app_xsltproc_fullpath, app_openssl_fullpath, app_xmllint_fullpath = library_openssl_xsltproc_xmllint()
        msj, app_openssl_fullpath= library_openssl_xsltproc_xmllint()
        if not app_openssl_fullpath:
            raise UserError(_("Error!"), _(
                "Failed to find in path '%s' app. This app is required for sign Mexican Electronic Invoice"%(app_openssl) ))
        cmd_params = ' -'.join(params)
        cmd_params = cmd_params and '-' + cmd_params or ''
        cmd = '"%s" x509 -inform "%s" -in "%s" -noout "%s" -out "%s"' % (
            app_openssl_fullpath, type, fname, cmd_params, fname_out)
        args = tuple(cmd.split(' '))
        # input, output = tools.exec_command_pipe(*args)
        input, output = exec_command_pipe(*args)
        result = self._read_file_attempts(output)
        input.close()
        output.close()
        return result

    


