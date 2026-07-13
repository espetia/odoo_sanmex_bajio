# -*- coding: utf-8 -*-
from .webservicerequest import WebServiceRequest
from lxml import etree as et
import xml.etree.ElementTree as ET
import base64
import logging
_logger = logging.getLogger(__name__)

class SolicitaDescarga(WebServiceRequest):

    xml_name = 'solicitadescarga.xml'
    soap_url = 'https://cfdidescargamasivasolicitud.clouda.sat.gob.mx/SolicitaDescargaService.svc'
    soap_action = 'http://DescargaMasivaTerceros.sat.gob.mx/ISolicitaDescargaService/SolicitaDescarga'
    solicitud_xpath = 's:Body/des:SolicitaDescarga/des:solicitud'
    result_xpath = 's:Body/SolicitaDescargaResponse/SolicitaDescargaResult'

    def solicitar_descarga(
        self, token, rfc_solicitante, fecha_inicial, fecha_final,
        rfc_emisor=None, rfc_receptor=None, tipo_solicitud='CFDI',
        tipo_comprobante=None, estado_comprobante=None, 
        rfc_a_cuenta_terceros=None, complemento=None, uuid=None
    ):

        arguments = {
            'RfcSolicitante': rfc_solicitante,
            'FechaFinal': fecha_final.strftime(self.DATE_TIME_FORMAT),
            'FechaInicial': fecha_inicial.strftime(self.DATE_TIME_FORMAT),
            'TipoSolicitud': tipo_solicitud,
            'TipoComprobante': tipo_comprobante,
            'EstadoComprobante': estado_comprobante,
            'RfcACuentaTerceros': rfc_a_cuenta_terceros,
            'Complemento': complemento,
            'UUID': uuid,
        }

        if rfc_emisor:
            arguments['RfcEmisor'] = rfc_emisor

        if rfc_receptor:
            arguments['RfcReceptores'] = [rfc_receptor]

        element_response = self.request(token, arguments)
        #resp_xml = etree.fromstring(element_response.text)

        #f_val = 's:Body/SolicitaDescargaResponse/SolicitaDescargaResult'

        #element_response = element_response.find(f_val)
        #xml_rot = et.parse(element_response).getroot()
        #xml = xml_rot.findall('IdSolicitud')
        #_logger.error('xml: %s', xml)
        
        #decodificado = base64.b64encode(str(element_response))
        #decodificado = base64.decodestring(element_response)
        #decodificado_1 = element_response.encode("utf-8")
        #parser = et.XMLParser(no_network=True)
        #xml_doc = et.ElementTree(et.fromstring(decodificado_1, parser))
        #xml_comprobante = xml_doc.getroot()   
        #_logger.error('xlm_comprobante: %s', xml_comprobante)
        enveloped = ET.fromstring(element_response.replace('\r\n',''))
        
        ret_val = {
            'id_solicitud': enveloped[0][0][0].attrib['IdSolicitud'],#element_response.get('IdSolicitud') or 'No encontrado',
            'cod_estatus': enveloped[0][0][0].attrib['CodEstatus'],#element_response.attrib['CodEstatus'],
            'mensaje': enveloped[0][0][0].attrib['Mensaje'],#element_response.attrib['Mensaje'] or 'No encontrado',
        }

        return ret_val
