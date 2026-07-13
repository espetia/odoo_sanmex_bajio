import base64
import hashlib
import subprocess
import tempfile
from datetime import datetime, timedelta
from io import BytesIO, StringIO
import requests
from OpenSSL import crypto
from lxml import etree
from odoo.exceptions import ValidationError

def remove_namespace(xml):
    # xml = etree.tostring(element_root).decode()
    xslt_remove_namespaces = '''<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
            <xsl:output method="xml" indent="no"/>
            <xsl:template match="/|comment()|processing-instruction()">
                <xsl:copy>
                  <xsl:apply-templates/>
                </xsl:copy>
            </xsl:template>
            <xsl:template match="*">
                <xsl:element name="{local-name()}">
                  <xsl:apply-templates select="@*|node()"/>
                </xsl:element>
            </xsl:template>
            <xsl:template match="@*">
                <xsl:attribute name="{local-name()}">
                  <xsl:value-of select="."/>
                </xsl:attribute>
            </xsl:template>
            </xsl:stylesheet>
            '''
    xslt_doc = etree.parse(BytesIO(xslt_remove_namespaces.encode('ascii')))
    remove_namespaces = etree.XSLT(xslt_doc)
    forgettable_characters = ['s', 'o', 'u', 'h']
    strings_to_erase = ['%s:' % (character) for character in forgettable_characters]
    for string in strings_to_erase:
        xml = xml.replace(string, '')
    xmlStream = StringIO(xml)
    tree = etree.parse(xmlStream)
    return remove_namespaces(tree)


def get_element(element_root, xpath):
    element = element_root.find(xpath)
    if element is None:
        raise ValidationError(f"{xpath} \n Element is not located in XML.")
    else:
        return element


def set_element(element, data):
    if element is None:
        raise ValidationError("Element is not there to set text.")
    else:
        element.text = data


class SAT:
    DATE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'
    external_nsmap = None

    def __init__(self, signature, key, password):
        self.certificate = crypto.load_certificate(crypto.FILETYPE_ASN1, base64.b64decode(signature))
        self.holder_vat = self.certificate.get_subject().x500UniqueIdentifier.split(' ')[0]
        self.key_pem = self.convert_key_cer_to_pem(base64.decodebytes(key), password.encode('UTF-8'))
        self.private_key = crypto.load_privatekey(crypto.FILETYPE_PEM, self.key_pem)

    # This function is in odoo already
    def convert_key_cer_to_pem(self, key, password, *args):
        # TODO compute it from a python way
        with tempfile.NamedTemporaryFile('wb', suffix='.key', prefix='edi.mx.tmp.') as key_file, \
                tempfile.NamedTemporaryFile('wb', suffix='.txt', prefix='edi.mx.tmp.') as pwd_file, \
                tempfile.NamedTemporaryFile('rb', suffix='.key', prefix='edi.mx.tmp.') as keypem_file:
            key_file.write(key)
            key_file.flush()
            pwd_file.write(password)
            pwd_file.flush()
            subprocess.call(('openssl pkcs8 -in %s -inform der -outform pem -out %s -passin file:%s' % (
                key_file.name, keypem_file.name, pwd_file.name)).split())
            key_pem = keypem_file.read()
        return key_pem

    def check_response(self, response: requests.Response, result_xpath):
        try:
            response_xml = remove_namespace(response.text)
            # response_xml = etree.fromstring(
            #     response.text,
            #     parser=etree.XMLParser(huge_tree=True)
            # )
        except Exception:
            raise Exception(response.text)
        if response.status_code != requests.codes['ok']:
            error = get_element(response_xml, 'Body/Fault/faultstring')
            # error = get_element(response_xml, 's:Body/s:Fault/faultstring', external_nsmap)
            raise Exception(error)
        return get_element(response_xml, result_xpath)
        # return get_element(response_xml, result_xpath, external_nsmap)

    def get_headers(self, soap_action, token=False):
        headers = {
            'Content-type': 'text/xml;charset="utf-8"',
            'Accept': 'text/xml',
            'Cache-Control': 'no-cache',
            'SOAPAction': soap_action,
            'Authorization': 'WRAP access_token="{}"'.format(token) if token else ''
        }
        return headers

    def sign(self, esignature_cer_bin, solicitud):
        values = {}

        # element_digest = hashlib.sha1(etree.tostring(solicitud.getparent(), method='c14n', exclusive=1)).digest()
        element_digest = base64.b64encode(hashlib.sha1(etree.tostring(solicitud)).digest()).decode('ascii')
        values['DV'] = element_digest
        element_to_sign = '<SignedInfo><CanonicalizationMethod ' \
                          'Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#"/><SignatureMethod ' \
                          'Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1"/><Reference><Transforms><Transform ' \
                          'Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#"/></Transforms><DigestMethod ' \
                          'Algorithm="http://www.w3.org/2000/09/xmldsig#sha1"/><DigestValue>{' \
                          'DV}</DigestValue></Reference></SignedInfo>'
        signed_info = base64.b64encode(crypto.sign(self.private_key, element_to_sign, 'sha1')).decode("UTF-8").replace(
            "\n", "")
        values['SV'] = signed_info
        values['CER'] = esignature_cer_bin.decode()
        d = self.certificate.get_issuer().get_components()
        cer_issuer = u','.join(['{key}={value}'.format(key=key.decode(), value=value.decode()) for key, value in d])
        values['IN'] = cer_issuer
        serial = str(self.certificate.get_serial_number())
        values['SN'] = serial
        body = '<Signature xmlns="http://www.w3.org/2000/09/xmldsig#"><SignedInfo><CanonicalizationMethod ' \
               'Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#"/><SignatureMethod ' \
               'Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1"/><Reference><Transforms><Transform ' \
               'Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#"/></Transforms><DigestMethod ' \
               'Algorithm="http://www.w3.org/2000/09/xmldsig#sha1"/><DigestValue>{DV}</DigestValue></Reference' \
               '></SignedInfo><SignatureValue>{SV}</SignatureValue><KeyInfo><X509Data><X509IssuerSerial' \
               '><X509IssuerName>{IN}</X509IssuerName><X509SerialNumber>{SN}</X509SerialNumber></X509IssuerSerial' \
               '><X509Certificate>{CER}</X509Certificate></X509Data></KeyInfo></Signature>'.format(**values)
        parser = etree.XMLParser(remove_blank_text=True)
        element_root = etree.fromstring(body, parser)
        solicitud.append(element_root)
        return solicitud

    def prepare_soap_download_data(self, esignature_cer_bin, arguments, solicitud):
        solicitud = etree.fromstring(solicitud)
        try:
            for key in arguments:
                if key != 'RfcReceptores' and arguments[key] != None:
                    solicitud.set(key, arguments[key])
            self.sign(esignature_cer_bin, solicitud)
            return etree.tostring(solicitud).decode()
        except Exception as e:
            raise ValidationError(f"Check SAT Credentials.\n {e}. \n {arguments}")

    def soap_generate_token(self, certificate: crypto.X509, private_key: crypto.PKey):
        soap_url = 'https://cfdidescargamasivasolicitud.clouda.sat.gob.mx/Autenticacion/Autenticacion.svc'
        soap_action = 'http://DescargaMasivaTerceros.gob.mx/IAutenticacion/Autentica'
        result_xpath = 'Body/AutenticaResponse/AutenticaResult'
        date_created = datetime.utcnow()
        date_expires = date_created + timedelta(seconds=300)
        date_created = date_created.isoformat()
        date_expires = date_expires.isoformat()

        data = '<u:Timestamp ' \
               'xmlns:u="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd" ' \
               'u:Id="_0">' \
               '<u:Created>{created}</u:Created>' \
               '<u:Expires>{expires}</u:Expires>' \
               '</u:Timestamp>'.format(created=date_created, expires=date_expires)
        digest_value = base64.b64encode(hashlib.sha1(data.encode()).digest()).decode('ascii')
        dataToSign = '<SignedInfo xmlns="http://www.w3.org/2000/09/xmldsig#">' \
                     '<CanonicalizationMethod Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#">' \
                     '</CanonicalizationMethod>' \
                     '<SignatureMethod Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1">' \
                     '</SignatureMethod><Reference URI="#_0">' \
                     '<Transforms><Transform Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#">' \
                     '</Transform></Transforms>' \
                     '<DigestMethod Algorithm="http://www.w3.org/2000/09/xmldsig#sha1"></DigestMethod>' \
                     '<DigestValue>{digest_value}</DigestValue>' \
                     '</Reference></SignedInfo>'.format(digest_value=digest_value)
        signature = base64.b64encode(crypto.sign(private_key, dataToSign, 'sha1')).decode('ascii')
        b64certificate = base64.b64encode(crypto.dump_certificate(crypto.FILETYPE_ASN1, certificate)).decode('ascii')
        xml = '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" ' \
              'xmlns:u="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd">' \
              '<s:Header><o:Security s:mustUnderstand="1" ' \
              'xmlns:o="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">' \
              '<u:Timestamp u:Id="_0"><u:Created>{created}</u:Created>' \
              '<u:Expires>{expires}</u:Expires></u:Timestamp>' \
              '<o:BinarySecurityToken u:Id="BinarySecurityToken" ' \
              'ValueType="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-x509-token-profile-1.0#X509v3" ' \
              'EncodingType="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-soap-message-security-1.0' \
              '#Base64Binary">{b64certificate}</o:BinarySecurityToken>' \
              '<Signature xmlns="http://www.w3.org/2000/09/xmldsig#"><SignedInfo>' \
              '<CanonicalizationMethod Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#"/>' \
              '<SignatureMethod Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1"/><Reference URI="#_0">' \
              '<Transforms><Transform Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#"/></Transforms>' \
              '<DigestMethod Algorithm="http://www.w3.org/2000/09/xmldsig#sha1"/>' \
              '<DigestValue>{digest_value}</DigestValue></Reference></SignedInfo>' \
              '<SignatureValue>{b64signature}</SignatureValue>' \
              '<KeyInfo><o:SecurityTokenReference><o:Reference ' \
              'ValueType="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-x509-token-profile-1.0#X509v3" ' \
              'URI="#BinarySecurityToken"/></o:SecurityTokenReference></KeyInfo></Signature></o:Security></s:Header>' \
              '<s:Body><Autentica xmlns="http://DescargaMasivaTerceros.gob.mx"/></s:Body></s:Envelope>'.format(
            created=date_created,
            expires=date_expires,
            b64certificate=b64certificate,
            digest_value=digest_value,
            b64signature=signature
        )
        soap_request = xml.encode('utf-8')
        communication = requests.post(
            soap_url,
            soap_request,
            headers=self.get_headers(soap_action),
            verify=True,
            timeout=15,
        )
        token = self.check_response(communication, result_xpath)
        self.token = token.text
        return token.text

    def soap_request_download(self, token, date_from=None, date_to=None, rfc_emisor=None, tipo_solicitud='CFDI',
                              tipo_comprobante=None, rfc_receptor=None,
                              estado_comprobante=None, rfc_a_cuenta_terceros=None, complemento=None, uuid=None):
        soap_url = 'https://cfdidescargamasivasolicitud.clouda.sat.gob.mx/SolicitaDescargaService.svc'
        soap_action = 'http://DescargaMasivaTerceros.sat.gob.mx/ISolicitaDescargaService/SolicitaDescarga'
        result_xpath = 'Body/SolicitaDescargaResponse/SolicitaDescargaResult'
        arguments = {
            'RfcSolicitante': self.holder_vat,
            'FechaInicial': date_from.isoformat(),
            'FechaFinal': date_to.isoformat(),
            'TipoSolicitud': tipo_solicitud,
            'TipoComprobante': tipo_comprobante,
            'EstadoComprobante': estado_comprobante,
            'RfcACuentaTerceros': rfc_a_cuenta_terceros,
            'Complemento': complemento,
            'UUID': uuid,
        }
        if rfc_emisor:
            arguments['RfcEmisor'] = self.holder_vat
        if rfc_receptor:
            arguments['RfcReceptores'] = self.holder_vat
        cer = base64.b64encode(crypto.dump_certificate(crypto.FILETYPE_ASN1, self.certificate))
        solicitud = '<des:solicitud xmlns:des="http://DescargaMasivaTerceros.sat.gob.mx" xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"><des:RfcReceptores><des:RfcReceptor>{}</des:RfcReceptor></des:RfcReceptores></des:solicitud>'.format(arguments['RfcReceptores'] if 'RfcReceptores' in arguments else '')
        solicitud = self.prepare_soap_download_data(cer, arguments, solicitud)
        element_root = "<s:Envelope xmlns:des=\"http://DescargaMasivaTerceros.sat.gob.mx\" xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\"><s:Header/><s:Body><des:SolicitaDescarga>{}</des:SolicitaDescarga></s:Body></s:Envelope>".format(solicitud)
        element_root = etree.fromstring(element_root)
        soap_request = etree.tostring(element_root, method='c14n', exclusive=1)
        communication = requests.post(
            soap_url,
            soap_request,
            headers=self.get_headers(soap_action, token),
            verify=True,
            timeout=15,
        )
        element_response = self.check_response(communication, result_xpath)
        ret_val = {
            'id_solicitud': element_response.get('IdSolicitud'),
            'cod_estatus': element_response.get('CodEstatus'),
            'mensaje': element_response.get('Mensaje')
        }
        #_logger.info(f"\n >>> {ret_val}")
        return ret_val

    def soap_verify_package(self, signature_holder_vat, id_solicitud, token):
        soap_url = 'https://cfdidescargamasivasolicitud.clouda.sat.gob.mx/VerificaSolicitudDescargaService.svc'
        soap_action = 'http://DescargaMasivaTerceros.sat.gob.mx/IVerificaSolicitudDescargaService/VerificaSolicitudDescarga'
        result_xpath = 'Body/VerificaSolicitudDescargaResponse/VerificaSolicitudDescargaResult'
        arguments = {
            'RfcSolicitante': signature_holder_vat,
            'IdSolicitud': id_solicitud,
        }
        cer = base64.b64encode(crypto.dump_certificate(crypto.FILETYPE_ASN1, self.certificate))
        solicitud = '<des:solicitud xmlns:des="http://DescargaMasivaTerceros.sat.gob.mx" xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"/>'
        solicitud = self.prepare_soap_download_data(cer, arguments, solicitud)
        element_root = '<s:Envelope xmlns:des="http://DescargaMasivaTerceros.sat.gob.mx" xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"><s:Header/><s:Body><des:VerificaSolicitudDescarga>{}</des:VerificaSolicitudDescarga></s:Body></s:Envelope>'.format(solicitud)
        element_root = etree.fromstring(element_root)
        soap_request = etree.tostring(element_root, method='c14n', exclusive=1)

        communication = requests.post(
            soap_url,
            soap_request,
            headers=self.get_headers(soap_action, token),
            verify=True,
            timeout=15,
        )
        element_response = self.check_response(communication, result_xpath)
        ret_val = {
            'cod_estatus': element_response.get('CodEstatus'),
            'estado_solicitud': element_response.get('EstadoSolicitud'),
            'codigo_estado_solicitud': element_response.get('CodigoEstadoSolicitud'),
            'numero_cfdis': element_response.get('NumeroCFDIs'),
            'mensaje': element_response.get('Mensaje'),
            'paquetes': []
        }
        for id_paquete in element_response.iter('IdsPaquetes'):
            ret_val['paquetes'].append(id_paquete.text)
        return ret_val

    def soap_download_package(self, signature_holder_vat, id_paquete, token):
        soap_url = 'https://cfdidescargamasiva.clouda.sat.gob.mx/DescargaMasivaService.svc'
        soap_action = 'http://DescargaMasivaTerceros.sat.gob.mx/IDescargaMasivaTercerosService/Descargar'
        result_xpath = 'Body/RespuestaDescargaMasivaTercerosSalida/Paquete'
        arguments = {
            'RfcSolicitante': signature_holder_vat,
            'IdPaquete': id_paquete,
        }
        cer = base64.b64encode(crypto.dump_certificate(crypto.FILETYPE_ASN1, self.certificate))
        solicitud = '<des:peticionDescarga xmlns:des="http://DescargaMasivaTerceros.sat.gob.mx" xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" />'
        solicitud = self.prepare_soap_download_data(cer, arguments, solicitud)
        element_root = '<s:Envelope xmlns:des="http://DescargaMasivaTerceros.sat.gob.mx"  xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"><s:Header/> <s:Body><des:PeticionDescargaMasivaTercerosEntrada>{}</des:PeticionDescargaMasivaTercerosEntrada></s:Body></s:Envelope>'.format(solicitud)
        element_root = etree.fromstring(element_root)
        soap_request = etree.tostring(element_root, method='c14n', exclusive=1)
        communication = requests.post(
            soap_url,
            soap_request,
            headers=self.get_headers(soap_action, token),
            verify=True,
            timeout=15,
        )
        element_response = self.check_response(communication, result_xpath)
        element = element_response.getparent().getparent().getparent()
        respuesta = get_element(element, 'Header/respuesta')
        ret_val = {
            'cod_estatus': respuesta.get('CodEstatus'),
            'mensaje': respuesta.get('Mensaje'),
            'paquete_b64': element_response.text,
        }
        return ret_val
