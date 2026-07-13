# -*- coding: utf-8 -*-
from .webservicerequest import WebServiceRequest
from lxml import etree as et
import xml.etree.ElementTree as ET


class VerificaSolicitudDescarga(WebServiceRequest):

    xml_name = 'verificasolicituddescarga.xml'
    soap_url = 'https://cfdidescargamasivasolicitud.clouda.sat.gob.mx/VerificaSolicitudDescargaService.svc'
    soap_action = 'http://DescargaMasivaTerceros.sat.gob.mx/IVerificaSolicitudDescargaService/VerificaSolicitudDescarga'
    solicitud_xpath = 's:Body/des:VerificaSolicitudDescarga/des:solicitud'
    result_xpath = 's:Body/VerificaSolicitudDescargaResponse/VerificaSolicitudDescargaResult'

    def verificar_descarga(self, token, rfc_solicitante, id_solicitud):

        arguments = {
            'RfcSolicitante': rfc_solicitante,
            'IdSolicitud': id_solicitud,
        }

        element_response = self.request(token, arguments)
        enveloped = ET.fromstring(element_response.replace('\r\n',''))

        ret_val = {
            'cod_estatus': enveloped[0][0][0].attrib['CodEstatus'],#element_response.get('CodEstatus'),
            'estado_solicitud': enveloped[0][0][0].attrib['EstadoSolicitud'],#element_response.get('EstadoSolicitud'),
            'codigo_estado_solicitud': enveloped[0][0][0].attrib['CodigoEstadoSolicitud'],#element_response.get('CodigoEstadoSolicitud'),
            'numero_cfdis': enveloped[0][0][0].attrib['NumeroCFDIs'],#element_response.get('NumeroCFDIs'),
            'mensaje': enveloped[0][0][0].attrib['Mensaje'],#element_response.get('Mensaje'),
            'paquetes': []
        }
        paquetes = enveloped[0][0][0]
        for paquete in paquetes:
            ret_val['paquetes'].append(paquete.text)
        """for id_paquete in element_response.iter('{{{}}}IdsPaquetes'.format(self.external_nsmap[''])):
            ret_val['paquetes'].append(id_paquete.text)"""

        return ret_val
