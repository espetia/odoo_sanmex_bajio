# -*- coding: utf-8 -*-
from .webservicerequest import WebServiceRequest
from lxml import etree as et
import xml.etree.ElementTree as ET

class DescargaMasiva(WebServiceRequest):

    xml_name = 'descargamasiva.xml'
    soap_url = 'https://cfdidescargamasiva.clouda.sat.gob.mx/DescargaMasivaService.svc'
    soap_action = 'http://DescargaMasivaTerceros.sat.gob.mx/IDescargaMasivaTercerosService/Descargar'
    solicitud_xpath = 's:Body/des:PeticionDescargaMasivaTercerosEntrada/des:peticionDescarga'
    result_xpath = 's:Body/RespuestaDescargaMasivaTercerosSalida/Paquete'

    def descargar_paquete(self, token, rfc_solicitante, id_paquete):

        arguments = {
            'RfcSolicitante': rfc_solicitante,
            'IdPaquete': id_paquete,
        }

        element_response = self.request(token, arguments)

        """respuesta = element_response.getparent().getparent().getparent().find(
            's:Header/h:respuesta', namespaces=self.external_nsmap
        )"""
        enveloped = ET.fromstring(element_response.replace('\r\n',''))

        respuesta = enveloped[0][0]
        RespuestaDescargaMasivaTercerosSalida = enveloped[1][0]

        ret_val = {
            'cod_estatus': respuesta.attrib['CodEstatus'],#respuesta.get('CodEstatus'),
            'mensaje': respuesta.attrib['Mensaje'],#respuesta.get('Mensaje'),
            'paquete_b64': RespuestaDescargaMasivaTercerosSalida[0].text,
        }

        return ret_val
