# -*- coding: utf-8 -*-

from django.contrib import admin
from django.contrib.auth.decorators import permission_required, login_required
from django.core.urlresolvers import reverse
from django.db.models import Max, Q, F, Prefetch
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.template.response import TemplateResponse
from django.views.decorators.http import require_safe, require_POST

from utils.functions import render_to_pdf, render_wk_to_pdf, render_to_pdf_weasy
import json
import itertools
import datetime
import logging

from models import *
from modelsResource import RelatorioPorTipoResource
from identificacao.models import Entidade, EnderecoDetalhe, Endereco
from outorga.models import Termo, Modalidade, Natureza_gasto, Item
from protocolo.models import Protocolo, ItemProtocolo
from financeiro.models import Pagamento

# Get an instance of a logger
logger = logging.getLogger(__name__)


# Gera uma lista dos protocolos conforme o termo selecionado.
@login_required
@require_safe
def ajax_escolhe_termo(request):
    retorno = []
     
    t = request.GET.get('id')
    if t:
        termo = Termo.objects.get(pk=int(t))
        protocolos = Protocolo.objects.filter(termo=termo)

        for p in protocolos:
            descricao = '%s: %s - %s' % (p.doc_num(), p.descricao2.__unicode__(), p.mostra_valor())
            retorno.append({'pk':p.pk, 'valor':descricao})
    
    if not retorno:
        retorno = [{"pk":"0", "valor":"Nenhum registro"}]

    retorno_json = json.dumps(retorno)
    return HttpResponse(retorno_json, content_type="application/json")



# Gera uma lista dos itens do protocolo conforme protocolo selecionado.
@login_required
@require_safe
def ajax_escolhe_protocolo(request):
    retorno = []
    id = request.GET.get('id')
    previous = request.GET.get('previous')

    if id and previous:
        t = Termo.objects.get(pk=int(previous))
        itens = ItemProtocolo.objects.filter(protocolo__id=int(id), protocolo__termo=t)

        for i in itens:
            descricao = '%s - %s (%s)' % (i.quantidade, i.descricao, i.mostra_valor())
            retorno.append({'pk':i.pk, 'valor': descricao})

        if not retorno:
            retorno = [{"pk":"0", "valor":"Nenhum registro"}]

    retorno_json = json.dumps(retorno)
    return HttpResponse(retorno_json, content_type="application/json")


@login_required
@require_safe
def ajax_escolhe_pagamento(request):
    retorno = []
    termo = request.GET.get('termo')
    numero = request.GET.get('numero')
    
    if termo and numero:
        pgt = Pagamento.objects.filter(protocolo__termo__id=termo)
        for p in pgt.filter(Q(conta_corrente__cod_oper__icontains=numero) | Q(protocolo__num_documento__icontains=numero)):
            if p.conta_corrente:
                descricao = 'Doc. %s, cheque %s, valor %s' % (p.protocolo.num_documento, p.conta_corrente.cod_oper, p.valor_fapesp)
            else:
                descricao = 'Doc. %s, valor %s' % (p.protocolo.num_documento, p.valor_patrocinio)

            retorno.append({'pk':p.pk, 'valor':descricao})

    if not retorno:
        retorno = [{"pk":"0", "valor":"Nenhum registro"}]
    
    retorno_json = json.dumps(retorno)
    return HttpResponse(retorno_json, content_type="application/json")


@login_required
@require_safe
def ajax_escolhe_detalhe(request):
    ed_id = request.GET.get('detalhe')
    detalhe = get_object_or_404(EnderecoDetalhe, pk=ed_id)

    retorno = []
    for ed in EnderecoDetalhe.objects.filter(detalhe=detalhe):
        retorno.append({'pk':ed.pk, 'valor':ed.__unicode__()})

    retorno_json = json.dumps(retorno)
    return HttpResponse(retorno_json, content_type="application/json")


@login_required
@require_safe
def ajax_escolhe_entidade(request):
    ent_id = request.GET.get('entidade')
    entidade = get_object_or_404(Entidade, pk=ent_id)

    retorno = []
    for ed in EnderecoDetalhe.objects.all().order_by('endereco', 'detalhe__complemento', 'complemento'):
        if ed.end.entidade == entidade:
            descricao = ed.__unicode__()
            
            retorno.append({'pk':ed.pk, 'valor':descricao})

    if not retorno:
        retorno = [{"pk":"0", "valor":"Nenhum registro"}]

    retorno_json = json.dumps(retorno)
    return HttpResponse(retorno_json, content_type="application/json")


@login_required
@require_safe
def ajax_escolhe_equipamento(request):
    """
    Faz a busca de equipamentos por diversos atributos.
    Utilizado para fazer o filtro de "Equipamentos" durante a tela de cadastro/modificação de patrimonio. 
    """
    
    retorno = []
    filtro = request.GET.get('num_doc')
    id_equipamento = request.GET.get('id_equipamento')
    
    if filtro:
        retorno = [{'pk':p.pk, 'valor':p.__unicode__(), 'selected':(str(p.pk) == id_equipamento)} \
                        for p in Equipamento.objects.filter(\
                             Q(tipo__nome__icontains=filtro)\
                            | Q(descricao__icontains=filtro)\
                            | Q(part_number__icontains=filtro)\
                            | Q(entidade_fabricante__sigla__icontains=filtro)\
                            | Q(entidade_fabricante__nome__icontains=filtro)\
                            | Q(modelo__icontains=filtro)\
                            | Q(ncm__icontains=filtro)\
                            | Q(ean__icontains=filtro)\
                            | Q(titulo_autor__icontains=filtro)\
                            | Q(isbn__icontains=filtro))] \
               or [{"pk":"0", "valor":"Nenhum registro"}]
        retorno_json = json.dumps(retorno)
    else:
        retorno = [{'pk':p.pk, 'valor':p.__unicode__(), 'selected':(str(p.pk) == id_equipamento)} \
                   for p in Equipamento.objects.all()]

    if not retorno:
        retorno = [{"pk":"0", "valor":"Nenhum registro"}]

    retorno_json = json.dumps(retorno)
    return HttpResponse(retorno_json, content_type="application/json")


@login_required
@require_safe
def ajax_get_marcas_por_termo(request):
    """
    Utilizado para montar dados de "Equipamentos" durante a tela de cadastro/modificação de patrimonio. 
    """
    retorno = []
    
    termo_id = request.GET.get('termo')

    if termo_id != None and (termo_id == '0' or termo_id == ''):
        patrimonios = Patrimonio.objects.filter(equipamento__entidade_fabricante__isnull=False).order_by('equipamento__entidade_fabricante__sigla').distinct('equipamento__entidade_fabricante__sigla')
    else:
        patrimonios = Patrimonio.objects.filter(pagamento__protocolo__termo_id=termo_id, equipamento__entidade_fabricante__isnull=False).order_by('equipamento__entidade_fabricante__sigla').distinct('equipamento__entidade_fabricante__sigla')
    
    retorno = [{'pk':p.equipamento.entidade_fabricante.pk, 'valor':p.equipamento.entidade_fabricante.__unicode__()} 
           for p in patrimonios]
    
    retorno_json = json.dumps(retorno)
    return HttpResponse(retorno_json, content_type="application/json")


@login_required
@require_safe
def ajax_get_equipamento(request):
    """
    Faz a busca de equipamentos
    Utilizado para montar dados de "Equipamentos" durante a tela de cadastro/modificação de patrimonio. 
    """
    retorno = []
    id_equipamento = request.GET.get('id_equipamento')
    p = Equipamento.objects.get(id=id_equipamento)
    
    marca = ''
    if p.entidade_fabricante:
        marca = p.entidade_fabricante.sigla
    
    retorno = {'pk':p.pk,
                'valor':p.__unicode__(),
                'modelo':p.modelo,
                'part_number':p.part_number,
                'marca':marca,
                'ean':p.ean,
              }
    
    retorno_json = json.dumps(retorno)
    return HttpResponse(retorno_json, content_type="application/json")


@login_required
@require_safe
def ajax_get_procedencia_filter_tipo(request):
    """
    AJAX para buscar procedencias de patrimonio filtrados por tipo 
    """
    retorno = []
    id_tipo = request.GET.get('id_tipo')
    entidades_ids = Patrimonio.objects.filter(tipo=id_tipo).order_by('tipo').values_list('entidade_procedencia', flat=True).distinct()
    
    procedencias = Entidade.objects.filter(id__in=entidades_ids)
    
    retorno = [{'pk':p.pk, 'valor':p.__unicode__()} 
               for p in procedencias]
    
    retorno_json = json.dumps(retorno)
    return HttpResponse(retorno_json, content_type="application/json")


@login_required
@require_safe
def ajax_escolhe_patrimonio(request):
    """
    Faz a busca de patrimonios que estao relacionados a NFs.
    Utilizado para fazer o filtro de "Patrimonios Contidos em" durante a tela de cadastro/modificação de patrimonio. 
    """
    
    retorno = []
    num_doc = request.GET.get('num_doc')
    
    if num_doc:
        retorno = [{'pk':p.pk, 'valor':p.__unicode__()} for p in Patrimonio.objects.filter(Q(pagamento__protocolo__num_documento__icontains=num_doc) | Q(ns__icontains=num_doc))] or [{"pk":"0", "valor":"Nenhum registro"}]
        retorno_json = json.dumps(retorno)

    if not retorno:
        retorno = [{"pk":"0", "valor":"Nenhum registro"}]

    retorno_json = json.dumps(retorno)
    return HttpResponse(retorno_json, content_type="application/json")


@login_required
@require_safe
def ajax_patrimonio_existente(request):
    retorno = {'marca':'', 'modelo':'', 'descricao':'', 'procedencia':''}
    part_number = request.GET.get('part_number')
    
    existentes = Patrimonio.objects.filter(equipamento__part_number__iexact=part_number)

    if part_number and existentes.count():
        p = existentes[0]
        
        retorno = {'marca':p.marca, 'modelo':p.modelo, 'descricao':p.descricao, 'procedencia':p.procedencia}

    retorno_json = json.dumps(retorno)
    return HttpResponse(retorno_json, content_type='application/json')


@login_required
def por_estado(request):
    if request.method == 'POST':
        if request.POST.get('estado'):
            estado_id = request.POST.get('estado')
            estado = get_object_or_404(Estado, pk=estado_id)

            no_estado = []
            for p in Patrimonio.objects.filter(patrimonio__isnull=True):
                ht = p.historico_atual
                if ht and ht.estado == estado:
                    no_estado.append(ht.id)

            no_estado = HistoricoLocal.objects.filter(id__in=no_estado)
            # entidades_ids = no_estado.values_list('endereco__endereco__entidade', flat=True).distinct()
            entidades_ids = []
            for h in no_estado:
                try:
                    entidades_ids.append(h.endereco.end.entidade.id)
                except:
		    pass
            entidades = []
            for e in Entidade.objects.filter(id__in=entidades_ids):
                detalhes = []
                # detalhes_ids = no_estado.values_list('endereco', flat=True).filter(endereco__endereco__entidade=e)
                detalhes_ids = [h.endereco.id for h in no_estado if h.endereco.end.entidade == e]
                for d in EnderecoDetalhe.objects.filter(id__in=detalhes_ids):
                    detalhes.append({'detalhe':d, 'patrimonio':Patrimonio.objects.filter(historicolocal__in=no_estado.filter(endereco=d))})
                entidades.append({'entidade':e, 'detalhes':detalhes})
            return TemplateResponse(request, 'patrimonio/por_estado.html', {'estado':estado, 'entidades':entidades})
    else:
        return TemplateResponse(request, 'patrimonio/sel_estado.html', {'estados':Estado.objects.all()})


@login_required
def por_tipo(request):
    if request.method == 'GET' and request.GET.get('tipo'):
        tipo_id = request.GET.get('tipo')
        tipo = get_object_or_404(Tipo, pk=tipo_id)
        
        procedencia = ''
        patrimonios = Patrimonio.objects.filter(tipo_id=tipo_id).order_by('entidade_procedencia', 'equipamento__entidade_fabricante', 'ns')
        if request.GET.get('procedencia') and request.GET.get('procedencia') != '':
            procedencia_id = request.GET.get('procedencia')
            patrimonios = patrimonios.filter(entidade_procedencia=procedencia_id)
            procedencia = Entidade.objects.get(id=procedencia_id)
            
#         patrimonios.select_related('entidade_procedencia', 'equipamento')

        patrimonios = patrimonios.select_related('entidade_procedencia', 'equipamento', 'equipamento__entidade_fabricante', 'pagamento', 'pagamento__protocolo')
        
        pdf = request.GET.get('acao') == '1'
        xls = request.GET.get('acao') == '2'
        if pdf:
            return render_to_pdf_weasy('patrimonio/por_tipo_weasy.pdf', {'tipo':tipo,
                                                                  'procedencia':procedencia,
                                                                  'patrimonios':patrimonios},
                                       request=request,
                                       filename="inventario_por_tipo.pdf")
        elif xls:
            # Export para Excel/XLS
            dataset = RelatorioPorTipoResource().export(queryset=patrimonios)
            
            response = HttpResponse(dataset.xls, content_type='application/vnd.ms-excel;charset=utf-8')
            response['Content-Disposition'] = "attachment; filename=relatorio_patrimonio_por_tipo.xls"
    
            return response
        else:

            # Listas para remontar o filtro de Tipos e o filtro e Procedencias
            tipos = Tipo.objects.all()
            entidades_ids = Patrimonio.objects.filter(tipo=tipo_id).order_by('tipo').values_list('entidade_procedencia', flat=True).distinct()
            procedencias = Entidade.objects.filter(id__in=entidades_ids)
        
            return TemplateResponse(request, 'patrimonio/por_tipo.html', {'tipos': tipos,
                                                                      'procedencias':procedencias,
                                                                      'tipo':tipo,
                                                                      'procedencia':procedencia,
                                                                      'patrimonios':patrimonios})
    else:
        tipos = Tipo.objects.all()
        return TemplateResponse(request, 'patrimonio/sel_tipo.html', {'tipos':tipos})


@login_required
def por_marca(request, pdf=0):
    if request.method == 'GET' and request.GET.get('marca'):
        marca = request.GET.get('marca')
        if pdf:
            return render_to_pdf_weasy('patrimonio/por_marca.pdf', {'marca':marca, 'patrimonios':Patrimonio.objects.filter(equipamento__entidade_fabricante__sigla=marca)}, request=request, filename='inventario_por_marca.pdf')
        return TemplateResponse(request, 'patrimonio/por_marca.html', {'marca':marca, 'patrimonios':Patrimonio.objects.filter(equipamento__entidade_fabricante__sigla=marca)})
    else:
        return TemplateResponse(request, 'patrimonio/sel_marca.html', {'marcas':Patrimonio.objects.values_list('equipamento__entidade_fabricante__sigla', flat=True).order_by('equipamento__entidade_fabricante__sigla').distinct()})


@login_required
def por_local(request, pdf=0):
    if request.GET.get('entidade') and request.GET.get('endereco'):
        atuais = []
        detalhes = []

        endereco_id = request.GET.get('endereco')
        detalhe_id = request.GET.get('detalhe2')
        
        if not detalhe_id:
           detalhe_id = request.GET.get('detalhe1')
        if not detalhe_id:
           detalhe_id = request.GET.get('detalhe')
   
        
        for p in Patrimonio.objects.filter(patrimonio__isnull=True).prefetch_related(Prefetch('historicolocal_set', queryset=HistoricoLocal.objects.all())):
            ht = p.historico_atual_prefetched
            if ht:
                 atuais.append(ht.id)
        
        # Listamos os patrimonios candidatos, a partir do filtro de endereços
        if detalhe_id:
            detalhe = get_object_or_404(EnderecoDetalhe, pk=detalhe_id)
            
            detalhes = []
            i = 0
            for ed in EnderecoDetalhe.objects.filter(pk=detalhe_id):
                detalhes.append(ed)
            
            while i < len(detalhes):
                for ed in detalhes[i].enderecodetalhe_set.all():
                    detalhes.append(ed)
                i += 1
                
            patrimonio_ids = HistoricoLocal.objects.filter(patrimonio__patrimonio__isnull=True, endereco__in=detalhes).values_list('patrimonio', flat=True).order_by('id')
        else:
            # Se não tiver filtro de detalhe, temos que buscar em todos os enderecos possiveis
            endereco = get_object_or_404(Endereco, pk=endereco_id)

            patrimonio_ids = HistoricoLocal.objects.filter(patrimonio__patrimonio__isnull=True, endereco__endereco=endereco).values_list('patrimonio', flat=True).order_by('id') \
                            | HistoricoLocal.objects.filter(patrimonio__patrimonio__isnull=True, endereco__detalhe__endereco=endereco).values_list('patrimonio', flat=True).order_by('id') \
                            | HistoricoLocal.objects.filter(patrimonio__patrimonio__isnull=True, endereco__detalhe__detalhe__endereco=endereco).values_list('patrimonio', flat=True).order_by('id')
        
        # Com os patrimonios candidatos, buscamos somente endereços que possuem
        # históricos atuais nos patrimonios
        atuais = []
        for p in Patrimonio.objects.filter(patrimonio__isnull=True, id__in=patrimonio_ids).prefetch_related('historicolocal_set'):
            ht = p.historico_atual_prefetched
            if ht:
                 atuais.append(ht.id)
           
        # Aqui listamos os Patrimonios que possuem Historico Atual no endereço selecionado
        if detalhe_id:
            historicos = HistoricoLocal.objects.filter(id__in=atuais, endereco__in=detalhes)
            context = {'detalhe':detalhe,
                       'det':detalhe_id,
                       'detalhes':[{'patrimonio':Patrimonio.objects.filter(historicolocal__in=historicos)
                                    .select_related('equipamento__entidade_fabricante', 'entidade_procedencia', 'pagamento__protocolo')
                                    .prefetch_related(Prefetch('historicolocal_set', queryset=HistoricoLocal.objects.select_related('estado'))) \
                                    .prefetch_related(Prefetch('contido', queryset=Patrimonio.objects.select_related('entidade_procedencia', 'pagamento__protocolo', 'equipamento__entidade_fabricante'))) \
                                    .prefetch_related(Prefetch('contido__historicolocal_set', queryset=HistoricoLocal.objects.select_related('estado'))) \
                                    .prefetch_related(Prefetch('contido__contido', queryset=Patrimonio.objects.select_related('entidade_procedencia', 'pagamento__protocolo', 'equipamento__entidade_fabricante'))) \
                                    .prefetch_related(Prefetch('contido__contido__historicolocal_set', queryset=HistoricoLocal.objects.select_related('estado'))) \
                                    .prefetch_related(Prefetch('contido__contido__contido', queryset=Patrimonio.objects.select_related('entidade_procedencia', 'pagamento__protocolo', 'equipamento__entidade_fabricante'))) \
                                    .prefetch_related(Prefetch('contido__contido__contido__historicolocal_set', queryset=HistoricoLocal.objects.select_related('estado'))) \
                                    .order_by('descricao', 'complemento')}]}
        else:
            endereco = get_object_or_404(Endereco, pk=endereco_id)
            
            historicos = HistoricoLocal.objects.filter(id__in=atuais, endereco__endereco=endereco
                                           ) | HistoricoLocal.objects.filter(id__in=atuais, endereco__detalhe__endereco=endereco
                                           ) | HistoricoLocal.objects.filter(id__in=atuais, endereco__detalhe__detalhe__endereco=endereco)
            detalhes = []
            detalhes_ids = historicos.values_list('endereco', flat=True)
            for d in EnderecoDetalhe.objects.filter(id__in=detalhes_ids):
                pat = {}
                detalhes.append({'detalhe':d, 'patrimonio': Patrimonio.objects.filter(historicolocal__in=historicos.filter(endereco=d)) \
                                                            .select_related('equipamento__entidade_fabricante', 'entidade_procedencia', 'pagamento__protocolo') \
                                                            .prefetch_related(Prefetch('historicolocal_set', queryset=HistoricoLocal.objects.select_related('estado'))) \
                                                            .order_by('descricao', 'complemento')
                                 })
            context = {'endereco':endereco, 'end':endereco_id, 'detalhes':detalhes, 'detalhe':'', 'det':'' }
        
        if pdf:
            return render_to_pdf_weasy('patrimonio/por_local_weasy.pdf', context, request=request, filename='inventario_por_local.pdf')
        return render_to_response('patrimonio/por_local.html', context, context_instance=RequestContext(request))
    else:
        entidades = find_entidades_filhas(None)
        msg = "A seleção da Entidade, Endereço e Localização são obrigatórios."
        return render_to_response('patrimonio/sel_local.html', {'entidades':entidades, 'msg':msg}, context_instance=RequestContext(request))


@login_required
def por_local_termo(request, pdf=0):
    if request.GET.get('entidade'):
        atuais = []
        # Buscando os históricos atuais de patrimonios de primeiro nível
        for p in Patrimonio.objects.filter(patrimonio__isnull=True):
            ht = p.historico_atual
            if ht:
                 atuais.append(ht.id)
        
        detalhe_id = request.GET.get('detalhe2')
        if not detalhe_id:
           detalhe_id = request.GET.get('detalhe1')
        if not detalhe_id:
           detalhe_id = request.GET.get('detalhe')
           
        endereco_id = request.GET.get('endereco')
        filtro_com_fmusp = request.GET.get('com_fmusp') or False

        if detalhe_id:
            detalhe = get_object_or_404(EnderecoDetalhe, pk=detalhe_id)
            detalhes = [detalhe]
            
            i = 0
            while i < len(detalhes):
                for ed in detalhes[i].enderecodetalhe_set.all():
                    detalhes.append(ed)
                i += 1
            
            historicos = HistoricoLocal.objects.filter(id__in=atuais, endereco__in=detalhes)
            
            ps = Patrimonio.objects.filter(historicolocal__in=historicos)
            if filtro_com_fmusp:
                ps = ps.filter(numero_fmusp__isnull=False)
            
            endereco = get_object_or_404(Endereco, pk=endereco_id)
            enderecos = []
            enderecos.append({'endereco':endereco, 'end':endereco_id, 'detalhes':[{'detalhe':detalhe, 'det':detalhe_id, 'patrimonio':iterate_patrimonio(ps, 0, filtro_com_fmusp)}]})
            context = {'detalhe':detalhe, 'det':detalhe_id, 'enderecos': enderecos}
            
        elif endereco_id and endereco_id != "":
            endereco_id = request.GET.get('endereco')
            
            enderecos = []
            endereco = find_endereco(atuais, endereco_id, filtro_com_fmusp)
            enderecos.append(endereco)
            context = {'enderecos': enderecos}
            
        else:
            entidade_id = request.GET.get('entidade')
            entidade_filha_id = request.GET.get('entidade1')
            
            if entidade_filha_id:
                # Se for selecionada a entidade de segundo nível, podemos utiliza-la como filtro
                entidade = Entidade.objects.filter(pk=entidade_filha_id)
            else:
                # Se for selecionada a entidade de primeiro nível, devemos fazer a busca incluindo todas as suas entidades de segundo nível
                entidade = Entidade.objects.filter(pk=entidade_id) | Entidade.objects.filter(entidade=entidade_id)
            enderecos = []
            for endereco in Endereco.objects.filter(entidade__in=entidade):    
                endereco = find_endereco(atuais, endereco.id, filtro_com_fmusp)
                if endereco:
                    enderecos.append(endereco)
            context = {'entidade': entidade, 'ent':entidade_id, 'enderecos': enderecos}
            
        if pdf:
            return render_to_pdf_weasy('patrimonio/por_local_termo_weasy.pdf', context, request=request, filename='inventario_por_local.pdf')
        else:
            return render_to_response('patrimonio/por_local_termo.html', context, RequestContext(request, context))
    else:
        # Cria a lista para o SELECT de filtro de Entidades, buscando as Entidades que possuem EnderecoDetalhe
        entidades = find_entidades_filhas(None)
        msg = "A seleção da Entidade é obrigatória."
        return render_to_response('patrimonio/sel_local_termo.html', {'entidades':entidades, 'msg':msg}, context_instance=RequestContext(request))


# Usado para criar o filtro de entidades.
# Caso o parametro seja None, busca todas as entidades de primeiro nível, seguidas pela busca de todas as entidades abaixo.
# Somente são consideradas Entidades válidas para a exibição no filtro as que possuirem EnderecoDetalhe, de qualquer nível de Entidade
def find_entidades_filhas(entidade_id):
    if entidade_id:
        entidades = Entidade.objects.filter(entidade=entidade_id)
    else:
        entidades = Entidade.objects.filter(entidade__isnull=True)
        
    entidades_retorno = []
    for entidade in entidades:
        entidades_filhas = find_entidades_filhas(entidade.id)
        entidade_valida = Entidade.objects.filter(id=entidade.id, endereco__isnull=False, endereco__enderecodetalhe__isnull=False,)
        
        if entidade_valida or len(entidades_filhas) > 0:
            entidades_retorno.append({"entidade": entidade, "filhas":entidades_filhas})
    
    return entidades_retorno


# Usado no disparo da view por_local_termo
# Busca patrimonios de um endereco
def find_endereco(atuais, endereco_id, filtro_com_fmusp=False):
    endereco = get_object_or_404(Endereco, pk=endereco_id)

    # busca os historicos de localizacao de patrimonio baseado no endereco
    # busca os que estiverem no endereço, ou localidades abaixo deste endereco
    historicos = HistoricoLocal.objects.filter(id__in=atuais, endereco__endereco=endereco
                                               ) | HistoricoLocal.objects.filter(id__in=atuais, endereco__detalhe__endereco=endereco
                                               ) | HistoricoLocal.objects.filter(id__in=atuais, endereco__detalhe__detalhe__endereco=endereco)
    detalhes = []
    detalhes_ids = historicos.values_list('endereco', flat=True)
    enderecoDetalhes = EnderecoDetalhe.objects.filter(id__in=detalhes_ids)
    for d in enderecoDetalhes:
        ps = Patrimonio.objects.filter(historicolocal__in=historicos.filter(endereco=d))
        if filtro_com_fmusp:
            ps = ps.filter(numero_fmusp__isnull=False)
        detalhes.append({'detalhe':d, 'patrimonio':iterate_patrimonio(ps, 0, filtro_com_fmusp)})
    
    context = None
    if len(detalhes) > 0:
        context = {'endereco':endereco, 'end':endereco_id, 'detalhes':detalhes}
    return context


def iterate_patrimonio(p_pts, nivel=0, filtro_com_fmusp=False):
    if nivel == 4 or len(p_pts) == 0:
        return
    
    patrimonios = []
    
    pts = p_pts
    if filtro_com_fmusp:
        pts = pts.filter(numero_fmusp__isnull=False)
    
    for p in pts:
        patrimonio = {}
        patrimonio.update({'id':p.id, 'termo':'', 'fmusp':p.numero_fmusp, 'num_documento':'',
                            'apelido':p.apelido, 'modelo':p.modelo, 'part_number':p.part_number, 'descricao':p.descricao,
                            'ns':p.ns, 'estado':'', 'posicao':'', 'contido':[]})
        if p.pagamento and p.pagamento.protocolo:
            patrimonio.update({'termo': str(p.pagamento.protocolo.termo)})
            patrimonio.update({'num_documento': p.pagamento.protocolo.num_documento})
            
        if p.historico_atual:
            patrimonio.update({'estado': p.historico_atual.estado})
            patrimonio.update({'posicao': p.historico_atual.posicao})
            
        
        contido = iterate_patrimonio(p.contido.all(), nivel + 1, filtro_com_fmusp)
        patrimonio.update({'contido': contido})
        
        patrimonios.append(patrimonio)
        
    patrimonios.sort(key=lambda p: p['posicao'], reverse=False)
    patrimonios.sort(key=lambda p: p['fmusp'], reverse=True)
    patrimonios.sort(key=lambda p: p['termo'], reverse=True)

    return patrimonios


@login_required
@require_safe
def por_tipo_equipamento(request, pdf=0):
    if len(request.GET) < 1:
        return TemplateResponse(request, 'patrimonio/sel_tipo_equip.html', {'tipos':TipoEquipamento.objects.all(), 'estados':Estado.objects.all(), 'pns':Equipamento.objects.values_list('part_number', flat=True).order_by('part_number').distinct()})

    tipo_id = request.GET.get('tipo')
    entidades = []
    if tipo_id == '0':
        patrimonios_tipo = Patrimonio.objects.all()
        tipo = 'todos'
    else:
        patrimonios_tipo = Patrimonio.objects.filter(equipamento__tipo__id=tipo_id)
        tipo = TipoEquipamento.objects.get(id=tipo_id)

    part_number = request.GET.get('partnumber')
    if part_number != '0':
        patrimonios_tipo = patrimonios_tipo.filter(equipamento__part_number=part_number)

    estado_id = request.GET.get('estado')
    for p in patrimonios_tipo \
        .select_related('equipamento__entidade_fabricante') \
        .prefetch_related(Prefetch('historicolocal_set', queryset=HistoricoLocal.objects.select_related('estado', 'endereco__detalhe', 'endereco__detalhe__endereco', 'endereco', 'endereco__endereco__entidade'))):
        if p.historico_atual_prefetched:
            if estado_id != '0':
                if p.historico_atual_prefetched.estado.id != int(estado_id):
                    continue
        
            ht = p.historico_atual_prefetched
            entidades.append({'entidade':ht.endereco.end.entidade, 'local':ht.endereco.complemento, 'patrimonio':p, 'posicao':ht.posicao})

    entidades.sort(key=lambda x: x['posicao'])
    entidades.sort(key=lambda x: x['local'])
    entidades.sort(key=lambda x: x['entidade'].sigla)

    entidade = ''
    local = ''
    for i in range(len(entidades)):
        if entidades[i]['entidade'] != entidade:
            entidade = entidades[i]['entidade']
            local = entidades[i]['local']
            continue
        if entidades[i]['local'] != local:
            local = entidades[i]['local']
            entidades[i]['entidade'] = ''
            continue

        entidades[i]['entidade'] = ''
        entidades[i]['local'] = ''

    return TemplateResponse(request, 'patrimonio/por_tipo_equipamento.html', {'entidades':entidades, 'tipo':tipo})


@login_required
@require_safe
def por_tipo_equipamento_old(request, pdf=0):
    if len(request.GET) < 1:
        return TemplateResponse(request, 'patrimonio/sel_tipo_equip.html', {'tipos':TipoEquipamento.objects.all(), 'estados':Estado.objects.all(), 'pns':Equipamento.objects.values_list('part_number', flat=True).order_by('part_number').distinct()})

    tipo_id = request.GET.get('tipo')
    entidades = []
    if tipo_id == '0':
        patrimonios_tipo = Patrimonio.objects.all()
        tipo = 'todos'
    else:
        patrimonios_tipo = Patrimonio.objects.filter(equipamento__tipo__id=tipo_id)
        tipo = TipoEquipamento.objects.get(id=tipo_id)

    estado_id = request.GET.get('estado')
    if estado_id != '0':
        for p in patrimonios_tipo:
            if p.historico_atual is None:
                patrimonios_tipo = patrimonios_tipo.exclude(id=p.id)
            elif p.historico_atual.estado.id != int(estado_id):
                patrimonios_tipo = patrimonios_tipo.exclude(id=p.id)

    part_number = request.GET.get('partnumber')
    if part_number != '0':
	patrimonios_tipo = patrimonios_tipo.filter(equipamento__part_number=part_number)

    for e in Entidade.objects.all():
        patrimonios_entidade = patrimonios_tipo.all()

        for p in patrimonios_entidade:
            if p.historico_atual is None:
                patrimonios_entidade = patrimonios_entidade.exclude(id=p.id)
            elif p.historico_atual.endereco.end.entidade != e:
                patrimonios_entidade = patrimonios_entidade.exclude(id=p.id)
        if patrimonios_entidade.count() > 0:
            entidade = {'entidade':e}
            locais = []
            for l in sorted(set([p.historico_atual.endereco.complemento for p in patrimonios_entidade])):
                patrimonios_local = patrimonios_entidade.all()
                for p in patrimonios_local:
                    if p.historico_atual is None:
                        patrimonios_local = patrimonios_local.exclude(id=p.id)
                    elif p.historico_atual.endereco.complemento != l:
			patrimonios_local = patrimonios_local.exclude(id=p.id)
                local = {'local':l, 'patrimonios':patrimonios_local}
	        locais.append(local)
            entidade['locais'] = locais
            entidades.append(entidade)
    
    return TemplateResponse(request, 'patrimonio/por_tipo_equipamento.html', {'entidades':entidades, 'tipo':tipo})


@login_required
@require_safe
def ajax_filtra_pn_estado(request):
    tipo_id = request.GET.get('id')
    if tipo_id == '0':
        part_numbers = Equipamento.objects.values_list('part_number', flat=True).order_by('part_number').distinct()
        patrimonios = Patrimonio.objects.all()
    else:
        part_numbers = Equipamento.objects.filter(tipo__id=tipo_id).values_list('part_number', flat=True).order_by('part_number').distinct()
        patrimonios = Patrimonio.objects.filter(equipamento__tipo__id=tipo_id)

    pns = []
    for p in part_numbers:
        pns.append({'pk':p, 'value':'%s (%s)' % (p, patrimonios.filter(equipamento__part_number=p).order_by('id').distinct().count())})

    estados = []
    for e in Estado.objects.all():
        patrimonios_estado = patrimonios.all()
        for p in patrimonios_estado:
            if not p.historico_atual:
                patrimonios_estado = patrimonios_estado.exclude(id=p.id)
            elif p.historico_atual.estado != e:
		patrimonios_estado = patrimonios_estado.exclude(id=p.id)

        estados.append({'pk':e.id, 'value':'%s (%s)' % (e, patrimonios_estado.order_by('id').distinct().count())})

    retorno = {'estados':estados, 'pns':pns}
    retorno_json = json.dumps(retorno)

    return HttpResponse(retorno_json, content_type="application/json")


@login_required
def por_termo(request, pdf=0):
    termo_id = request.GET.get('termo') or request.POST.get('termo') 
    modalidade = request.GET.get('modalidade') or request.POST.get('modalidade')
    agilis = request.GET.get('agilis') or request.POST.get('agilis')
    doado = request.GET.get('doado') or request.POST.get('doado')
    localizado = request.GET.get('localizado') or request.POST.get('localizado')
    numero_fmusp = request.GET.get('numero_fmusp') or request.POST.get('numero_fmusp')
    ver_numero_fmusp = request.GET.get('ver_numero_fmusp') or request.POST.get('ver_numero_fmusp')
    marcas = request.GET.getlist('marca') or request.POST.getlist('marca')
    
    template_name = 'por_termo'

    # Se não tiver Termo selecionado, volta para a tela de seleção de filtros.
    filtro_patrimonios = Patrimonio.objects.filter(pagamento__protocolo__termo_id=termo_id, equipamento__entidade_fabricante__isnull=False) \
                                            .only('equipamento__entidade_fabricante') \
                                            .select_related('equipamento__entidade_fabricante') \
                                            .order_by('equipamento__entidade_fabricante__sigla') \
                                            .distinct('equipamento__entidade_fabricante__sigla')
    filtro_marcas = [p.equipamento.entidade_fabricante for p in filtro_patrimonios]
    filtro_termos = Termo.objects.all()
    if termo_id is None:
        return TemplateResponse(request, 'patrimonio/escolhe_termo.html', {'filtro_termos':filtro_termos, 'filtro_marcas':filtro_marcas})

    if termo_id != '0':
        qs = Termo.objects.filter(id=termo_id)
    else:
        qs = Termo.objects.exclude(id=9)

    termos = []

    if agilis == '0':
        patrimonios = Patrimonio.objects.filter(agilis=False)
    elif agilis == '1':
        patrimonios = Patrimonio.objects.filter(agilis=True)
    else:
        patrimonios = Patrimonio.objects.all()

    if doado == '0':
        patrimonios = patrimonios.exclude(historicolocal__endereco__endereco__entidade__recebe_doacao=True, historicolocal__estado__id=1)
    elif doado == '1':
        patrimonios = patrimonios.filter(historicolocal__endereco__endereco__entidade__recebe_doacao=True)

    if localizado == '1':
        patrimonios = patrimonios.exclude(historicolocal__endereco__complemento__icontains='Localizado')
    elif localizado == '0':
        patrimonios = patrimonios.filter(historicolocal__endereco__complemento__icontains='Localizado')

    if modalidade == '1':
        patrimonios = patrimonios.filter(pagamento__origem_fapesp__item_outorga__natureza_gasto__modalidade__sigla__in=['MPN', 'MPI'])
    elif modalidade == '2':
        patrimonios = patrimonios.filter(pagamento__origem_fapesp__item_outorga__natureza_gasto__modalidade__sigla__in=['MCN', 'MCI'])

    if numero_fmusp == '1':
        patrimonios = patrimonios.filter(numero_fmusp__isnull=False)
    elif numero_fmusp == '0':
        patrimonios = patrimonios.filter(numero_fmusp__isnull=True)
    
    if marcas and len(marcas) > 0:
        filter_marcas = []
        for m in marcas:
            if m and m != '0':
                filter_marcas.append(m)
        if len(filter_marcas) > 0:
            patrimonios = patrimonios.filter(equipamento__entidade_fabricante__id__in=filter_marcas)

    patrimonios = patrimonios.select_related('equipamento__entidade_fabricante', 'equipamento__tipo')

    for t in qs:
        termo = {'termo':t}
        tps = []
        pat_termo = patrimonios.filter(pagamento__protocolo__termo=t)
        if numero_fmusp == '1':
            termo.update({'patrimonios':pat_termo.order_by('numero_fmusp', 'descricao', 'complemento')})
            termos.append(termo)
            # continue

        tipos = pat_termo.values_list('tipo', flat=True).order_by('tipo').distinct()
        for tipo in Tipo.objects.filter(id__in=tipos):
            tp = {'tipo':tipo}
            pgtos = []
            pt = pat_termo.filter(tipo=tipo)
            pagtos = pt.values_list('pagamento', flat=True).order_by('numero_fmusp').distinct()
            for pg in Pagamento.objects.filter(id__in=pagtos).select_related('protocolo'):
                pgto = {'pg': pg, 'patrimonios':pt.filter(pagamento=pg).order_by('numero_fmusp', 'descricao', 'complemento')}
                pgtos.append(pgto)
            tp.update({'pagamentos':pgtos})
            tps.append(tp)
        termo.update({'tipos':tps})
        termos.append(termo)
        
    if pdf:
        vars = {'termo':qs[0],
                'termos':termos,
                'i':itertools.count(1),
                'numero_fmusp':numero_fmusp,
                'ver_numero_fmusp':ver_numero_fmusp, }
        if termo_id != 0 and len(qs) > 0:
            vars.update({'t':qs[0]})
        return render_to_pdf_weasy('patrimonio/%s.pdf' % template_name, vars, request=request, filename='inventario_por_termo.pdf')
    else:
        
        return TemplateResponse(request, 'patrimonio/%s.html' % template_name, {'termos':termos,
                                                                                'i':itertools.count(1),
                                                                                'termo':qs[0],
                                                                                'modalidade':modalidade,
                                                                                'agilis':agilis,
                                                                                'doado':doado,
                                                                                'localizado':localizado,
                                                                                'marca':marcas,
                                                                                'numero_fmusp':numero_fmusp,
                                                                                'ver_numero_fmusp':ver_numero_fmusp,
                                                                                'filtro_marcas':filtro_marcas,
                                                                                'filtro_termos':filtro_termos,
                                                                                })


@login_required
def racks(request):
        
    # Busca os endereços que possuem Racks no estadoAtivos
    locais = EnderecoDetalhe.objects.filter(historicolocal__estado__id=Estado.PATRIMONIO_ATIVO, \
                                            historicolocal__patrimonio__equipamento__tipo__nome='Rack', \
                                            mostra_bayface=True,).order_by('id').distinct()
                                            
    
    todos_dcs = []
    for local in locais:
        dc = {'nome':local.complemento, 'id':local.id}
        todos_dcs.append(dc)

    p_dc = request.GET.get('dc')
    
    dcs = []
    if p_dc != None:
        if int(p_dc) > 0:
            locais = EnderecoDetalhe.objects.filter(id=p_dc)
        
        for local in locais:
            racks = []
            
            
            patrimonio_racks = Patrimonio.objects.filter(equipamento__tipo__nome='Rack', historicolocal__endereco__id=local.id).select_related('contido').prefetch_related('historicolocal_set')
            patrimonio_racks = list(patrimonio_racks)
            # Ordena os racks pela posição. Ex: R042 - ordena pela fila 042 e depois pela posição R
            patrimonio_racks.sort(key=lambda x: x.historico_atual.posicao_rack_letra, reverse=False)
            patrimonio_racks.sort(key=lambda x: x.historico_atual.posicao_rack_numero, reverse=True)
                
            fileiras = []
            rack_anterior = None
            for rack in patrimonio_racks:
                if not rack_anterior or rack.historico_atual.posicao_rack_numero != rack_anterior.historico_atual.posicao_rack_numero:
                    racks = []
                    fileiras.append({'racks': racks})
                    rack_anterior = rack
                    
                espaco_ocupado = 0
                equipamentos = []
                equipamentos_fora_visao = []
                equipamentos_pdu = []
                conflitos = []
                
                eixoY = 0
                if rack.tamanho:
                    rack_altura = int(rack.tamanho) * 3
                else:
                    # ISSO É UM PROBLEMA DE DADOS INVÁLIDOS. PRECISA SER TRATADO
                    rack_altura = 126
                    rack.tamanho = 42
                    conflitos.append({'obs': 'Rack não possui tamanho.'})
                
                # ordena os equipamentos do rack conforme a posição no rack
#                 pts = list(rack.contido.filter(historicolocal__posicao__isnull=False).values('historicolocal__data').aggregate(Max('historicolocal__data')))
                hist = rack.contido.annotate(hist=Max('historicolocal__data')).values_list('pk')
                pts = list(rack.contido.filter(pk__in=hist).select_related('equipamento', 'equipamento__tipo'))
                pts.sort(key=lambda x: x.historico_atual.posicao_furo, reverse=True)
    
                ptAnterior = None
                for pt in pts:
                    pos = pt.historico_atual.posicao_furo - 1 
                    
                    tamanho = 0
                    if pt.tamanho:
                        tamanho = pt.tamanho
                    # calculando a altura em furos
                    tam = int(round(tamanho * 3))
    
                    # calculo da posição em pixel do eixoY, top-down
                    eixoY = int(round(((rack_altura - (pos) - tam) * 19) / 3))
                    
                    # Setando Imagem do equipamento
                    imagem = None
                    imagem_traseira = None 
                    if pt.equipamento and pt.equipamento.imagem:
                        imagem = pt.equipamento.imagem.url
                    if pt.equipamento and pt.equipamento.imagem_traseira:
                        imagem_traseira = pt.equipamento.imagem_traseira.url
                        
                    # Verificando profundidade
                    # Assinala somente se ocupa a profundidade toda, ou somente metade 
                    # da profundidade do rack
                    profundidade = 1.0
                    if rack.equipamento.dimensao_id and pt.equipamento.dimensao_id:
                        if pt.equipamento.dimensao.profundidade < \
                            rack.equipamento.dimensao.profundidade / 2:
                            profundidade = 0.5
                    
                    flag_traseiro = False
                    if pt.historico_atual.posicao_colocacao in ('TD', 'TE', 'T', 'T01', 'T02', 'T03'):
                        flag_traseiro = True
                        
                    last_equipamento = {'id': pt.id, 'pos':pos, 'tam': tam, 'eixoY': eixoY, 'altura':(tam * 19 / 3),
                                              'pos_original':pt.historico_atual.posicao_furo,
                                              'imagem':imagem, 'imagem_traseira':imagem_traseira,
                                              'profundidade':profundidade,
                                              'nome':pt.apelido, 'descricao':pt.descricao or u'Sem descrição',
                                              'conflito':False, 'pos_col':pt.historico_atual.posicao_colocacao,
                                              'flag_traseiro':flag_traseiro}
                        
                    if pt.equipamento and pt.equipamento.tipo and 'tomada' in pt.equipamento.tipo.nome and \
                        pt.historico_atual.posicao_colocacao in ('TD', 'TE', 'lD', 'lE', 'LD', 'LE'):
                        
                        # Guardando as calhas de tomadas para apresentar nas laterais do Rack
                        equipamentos_pdu.append(last_equipamento)
                    elif pos < 0 or pt.historico_atual.posicao_colocacao in ('TD', 'TE', 'piso', 'lD', 'lE'):
                        if pos < 0: 
                            pos = '-'
                            last_equipamento['pos'] = pos
                        equipamentos_fora_visao.append(last_equipamento)
                        continue
                    else:
                        # x a partir do topo do container
                        # Adiciona os equipamentos frontais e traseiros. 
                        # O layout deve ser tratado no template
                        equipamentos.append(last_equipamento)
                        espaco_ocupado += tam
                    
                    # # CHECAGEM DE PROBLEMAS
#                     if pos <= 0:
#                         obs = 'Equip. com problema de posicionamento.'
#                         conflitos.append({'obs': obs, 'eq1':last_equipamento})
#                         last_equipamento['conflito'] = True 
#                     elif pt.tamanho is None:

                    if pt.tamanho is None:
                        obs = 'Equip. com tamanho ZERO.'
                        conflitos.append({'obs': obs, 'eq1':last_equipamento})
                        last_equipamento['conflito'] = True 
                    elif pos + (tam) > rack_altura:
                        # Ocorre quando um equipamento está passando do limite máximo do rack
                        # obs = '{!s} + {!s} > {!s}'.format(pos, (tam), 126)
                        obs = 'Equip. acima do limite do rack.'
                        conflitos.append({'obs': obs, 'eq1':last_equipamento})
                        last_equipamento['conflito'] = True
                
                    elif len(equipamentos) >= 2 and eixoY:
                        # Ocorre quando um equipamento sobrepoe o outro
                        # Caso estejam na mesma posição 01 ou 02, ou então, haja um equipamento que ocupe toda largura do rack
                        # Não ocorre quando os equipamentos estiverem lado a lado (marcados no attr pos_col, por exemplo, 01 com 02)

                        if ptAnterior and \
                            ptAnterior['profundidade'] + last_equipamento['profundidade'] <= 1.0 and \
                            ptAnterior['eixoY'] + ptAnterior['tam'] > eixoY and \
                            (ptAnterior['pos_col'] == last_equipamento['pos_col'] or not ptAnterior['pos_col'] or not last_equipamento['pos_col']):
                        
                            obs = 'Equipamentos sobrepostos.'
                            conflitos.append({'obs': obs, 'eq1':ptAnterior, 'eq2':last_equipamento})
                            last_equipamento['conflito'] = True
                            equipamentos[-2]['conflito'] = True
                    elif pos == -2:
                        # Posição -2 significa que o patrimonio não possui furo.
                        obs = 'Equip. sem posição definida.'
                        conflitos.append({'obs': obs, 'eq1':last_equipamento})
                        last_equipamento['conflito'] = True
                    elif pos < 0:
                        # Posição negativa
                        # Ocorre quando o equipamento não tem uma posição válida
                        obs = 'Equip. abaixo do limite do rack.'
                        conflitos.append({'obs': obs, 'eq1':last_equipamento})
                        last_equipamento['conflito'] = True
                    elif len(equipamentos) > 0 and last_equipamento['pos_col'] and last_equipamento['pos_col'] not in ('01', '02', 'T', 'TD', 'TE', 'T01', 'T02', 'piso', 'lD', 'lE', 'LD', 'LE'):
                        obs = 'Posicao inválida %s' % pt.historico_atual.posicao_colocacao
                        conflitos.append({'obs': obs, 'eq1':last_equipamento},)
                        last_equipamento['conflito'] = True
                        
                    ptAnterior = last_equipamento

                rack = {'id':rack.id,
                        'altura':int(rack.tamanho) * 3.0, 'altura_pts': rack.tamanho, 'altura_pxs': int(rack.tamanho) * 19.0,
                        'nome':rack.apelido, 'marca': rack.marca, 'local': pt.historico_atual.posicao,
                        'equipamentos':equipamentos, 'equipamentos_fora_visao':equipamentos_fora_visao,
                        'equipamentos_pdu':equipamentos_pdu,
                        'conflitos':conflitos}
                
                # Calculo de uso do rack                
                rack['vazio'] = '%.2f%%' % ((espaco_ocupado * 100.0) / (rack['altura'])) 
                racks.append(rack)
                
            dcEntidade = Entidade.objects.filter(endereco__enderecodetalhe=local)
            
            dc = {'nome':local.complemento, 'fileiras':fileiras, 'id':local, 'entidade': dcEntidade[0].sigla, }
            dcs.append(dc)
    
    chk_stencil = request.GET.get('chk_stencil') if request.GET.get('chk_stencil') else 1
    chk_legenda = request.GET.get('chk_legenda') if request.GET.get('chk_legenda') else 1
    chk_legenda_desc = request.GET.get('chk_legenda_desc') if request.GET.get('chk_legenda_desc') else 0
    chk_outros = request.GET.get('chk_outros') if request.GET.get('chk_outros') else 1
    chk_avisos = request.GET.get('chk_avisos') if request.GET.get('chk_avisos') else 1
    chk_traseira = request.GET.get('chk_traseira') if request.GET.get('chk_traseira') else 0
            
    if request.GET.get('pdf') == "2":
        return render_wk_to_pdf('patrimonio/racks-wk.pdf', {'dcs':dcs, 'todos_dcs':todos_dcs, 'chk_legenda':chk_legenda, 'chk_legenda_desc':chk_legenda, 'chk_legenda_desc':chk_legenda_desc, 'chk_stencil':chk_stencil, 'chk_outros':chk_outros, 'chk_avisos':chk_avisos, 'chk_traseira':chk_traseira}, request=request, filename='diagrama_de_racks.pdf',)
    elif request.GET.get('pdf'):
        return TemplateResponse(request, 'patrimonio/racks-wk.pdf', {'dcs':dcs, 'todos_dcs':todos_dcs, 'chk_legenda':chk_legenda, 'chk_legenda_desc':chk_legenda_desc, 'chk_stencil':chk_stencil, 'chk_outros':chk_outros, 'chk_avisos':chk_avisos, 'chk_traseira':chk_traseira})
    else:
        return TemplateResponse(request, 'patrimonio/racks.html', {'dcs':dcs, 'todos_dcs':todos_dcs, 'chk_legenda':chk_legenda, 'chk_legenda_desc':chk_legenda_desc, 'chk_stencil':chk_stencil, 'chk_outros':chk_outros, 'chk_avisos':chk_avisos, 'chk_traseira':chk_traseira})


@login_required
def racks1(request):
    detalhes = [ed for ed in EnderecoDetalhe.objects.filter(complemento__contains='.F', tipo__nome__startswith='Posi').order_by('-complemento') if len(ed.complemento.split('.')) == 2 and ed.end.id == 60]
    racks = []
    r = ''
    rack = ''
    alt = 0
    vazio = 0
    for ed in detalhes:
        equipamentos = []
        info = ed.complemento.split('.')
        if info[0] != r:
            if alt > 1: 
                equipamentos.append({'tamanho':alt - 1, 'range':range(alt - 2)})
		vazio += alt - 1
            r = info[0]
            if rack:
                rack['vazio'] = '%.2f%%' % ((rack['altura'] - vazio) * 100.0 / rack['altura'],)
                racks.append(rack)
            equipamentos = []
            rack = {'nome':r, 'altura':126, 'equipamentos':equipamentos}
            alt = 127
            vazio = 0
        hl = HistoricoLocal.objects.filter(endereco=ed, patrimonio__patrimonio__isnull=True)
        if hl.count() > 0:
            pt = hl[0].patrimonio
            try:
                pos = int(info[1][1:])
            except: continue
            if pos == 1 or pt.tamanho is None: continue
            if alt > pos + int(round(pt.tamanho * 3)):
                tam = alt - (pos + int(round(pt.tamanho * 3)))
                alt -= tam
                equipamentos.append({'tamanho':tam, 'range':range(tam - 1)})
                vazio += tam
            tam = int(round(pt.tamanho * 3))
            alt -= tam
            imagem = None
            if pt.equipamento:
                if pt.equipamento.imagem:
		    imagem = pt.equipamento.imagem.url
            equipamentos.append({'tamanho':tam, 'imagem':imagem, 'descricao':pt.descricao or u'Sem descrição', 'range':range(tam - 1)})

    return TemplateResponse(request, 'patrimonio/racks.html', {'racks':racks})
    # return render_to_pdf('patrimonio/racks.pdf', {'racks':racks})


@login_required
def presta_contas(request):
    termos = []
    for t in Termo.objects.all():
        termo = {'termo':t}
        termos.append(termo)

    return TemplateResponse(request, 'patrimonio/presta_contas.html', {'termos':termos})


@login_required
@require_safe
def ajax_abre_arvore(request):
    ret = []
    if request.GET.get('id'):
        id = request.GET.get('id')
        model = request.GET.get('model')
        if model == 'termo':
	    for n in Termo.objects.get(id=id).natureza_gasto_set.filter(item__origemfapesp__pagamento__patrimonio__isnull=False).distinct():
	        ret.append({'data':n.modalidade.sigla, 'attr':{'style':'padding-top:4px;', 'o_id':n.id, 'o_model': n._meta.module_name}})
        elif model == 'natureza_gasto':
            for i in Natureza_gasto.objects.get(id=id).item_set.filter(origemfapesp__pagamento__patrimonio__isnull=False).distinct():
                ret.append({'data':i.__unicode__(), 'attr':{'style':'padding-top:4px;', 'o_id':i.id, 'o_model': i._meta.module_name}})
        elif model == 'item':
            for o in Item.objects.get(id=id).origemfapesp_set.filter(pagamento__patrimonio__isnull=False).distinct():
                for p in o.pagamento_set.filter(patrimonio__isnull=False).distinct():
                    ret.append({'data':'%s %s' % (p.protocolo.tipo_documento.sigla or '', p.protocolo.num_documento), 'attr':{'style':'padding-top:4px;', 'o_id':p.id, 'o_model':p._meta.module_name}})
        elif model == 'pagamento':
            for pt in Pagamento.objects.get(id=id).patrimonio_set.all():
                ret.append({'data':'<div><div class="col1"></div><div class="col2"><div class="menor">%s</div><div class="maior">%s</div><div class="maior">%s - %s</div><div class="medio">%s</div><div class="menor">%s</div><div class="menor">%s</div><div class="menor">%s</div></div><div style="clear:both;"></div></div>' % (pt.tipo, pt.ns, pt.descricao, pt.complemento, pt.equipamento.tipo, pt.valor, 'Sim' if pt.agilis else u'Não', 'Sim' if pt.checado else u'Não'), 'attr':{'style':'height:130px;'}})
    else:
        for t in Termo.objects.all():
	    ret.append({'data':t.__unicode__(), 'attr':{'style':'padding-top:6px;', 'o_id':t.id, 'o_model': t._meta.module_name}})
    retorno_json = json.dumps(ret)
    return HttpResponse(retorno_json, content_type="application/json")


@login_required
def por_tipo_equipamento2(request):
    return TemplateResponse(request, 'patrimonio/por_tipo_equipamento2.html')


@login_required
@require_safe
def ajax_abre_arvore_tipo(request):
    ret = []
    if request.GET.get('id'):
        id = request.GET.get('id')
        model = request.GET.get('model')
        if model == 'tipoequipamento':
            for e in TipoEquipamento.objects.get(id=id).equipamento_set.all():
                ret.append({'data':e.descricao, 'attr':{'style':'padding-top:4px;', 'o_id':e.id, 'o_model': e._meta.module_name}})
        elif model == 'equipamento':
            patrimonios = list(Equipamento.objects.get(id=id).patrimonio_set.all())
            try:
                patrimonios.sort(key=lambda x:x.historico_atual.endereco.end.entidade.sigla)
            except:
                pass

            if patrimonios and len(patrimonios):
                retPatrimonio = u'<div><div class="col1"></div><div class="col2">'
                retPatrimonio += u'<table><tr class="col2"><th class="th_1"><div>Entidade</div></th><th class="th_2"><div>Local</div></th>'
                retPatrimonio += u'<th class="th_3"><div>Posição</div></th><th class="th_4"><div>Marca</div></th>'
                retPatrimonio += u'<th class="th_5"><div>Modelo</div></th><th class="th_6"><div>Part number</div></th>'
                retPatrimonio += u'<th class="th_7"><div>NS</div></th><th class="th_8"><div>Estado</div></th></tr>' 
                for p in patrimonios:
                    ha = p.historico_atual
                    pUrl = reverse('admin:patrimonio_patrimonio_change', args=(p.id,))
                    r = u'<tr class=""><td class="td_1"><div><a href="%s" target="_blank">%s</a></div></td>' % (pUrl, ha.endereco.end.entidade if ha else 'ND') 
                    r += u'<td class="td_2"><a href="%s" target="_blank"><div>%s</a></div></td>' % (pUrl, ha.endereco.complemento if ha else 'ND')
                    r += u'<td class="td_3"><a href="%s" target="_blank"><div>%s</a></div></td>' % (pUrl, ha.posicao if ha and ha.posicao else 'ND')
                    
                    eq_fabricante = ''
                    eq_modelo = ''
                    eq_part_number = ''
                    if p.equipamento:
                        if p.equipamento.entidade_fabricante:
                            eq_fabricante = p.equipamento.entidade_fabricante.sigla
                        if p.equipamento.modelo:
                            eq_modelo = p.equipamento.modelo
                        if p.equipamento.part_number:
                            eq_part_number = p.equipamento.part_number

                            
                    r += u'<td class="td_4"><a href="%s" target="_blank"><div>%s</a></div></td>' % (pUrl, eq_fabricante)
                    r += u'<td class="td_5"><a href="%s" target="_blank"><div>%s</a></div></td>' % (pUrl, eq_modelo)
                    r += u'<td class="td_6"><a href="%s" target="_blank"><div>%s</a></div></td>' % (pUrl, eq_part_number)
                    
                    r += u'<td class="td_7"><a href="%s" target="_blank"><div>%s</a></div></td>' % (pUrl, p.ns)
                    r += u'<td class="td_8"><a href="%s" target="_blank"><div>%s</a></div></td>' % (pUrl, ha.estado if ha else 'ND')
                    retPatrimonio = '%s %s' % (retPatrimonio, r) 
                retPatrimonio += '</table></div><div style="clear:both;"></div></div>'
                ret.append({'data':retPatrimonio, 'attr':{'style':'padding-top:4px; height:%spx' % ((1 + len(patrimonios)) * 20)}})
    else:
        for tp in TipoEquipamento.objects.all():
            # ret.append({'data':'%s <a onclick="$(\'#blocos\').jstree(\'open_all\', \'#%s-%s\')" style="color:#0000aa;">Abrir tudo</a>' % (tp.__unicode__(), tp._meta.module_name, tp.id), 'attr':{'id':'%s-%s'% (tp._meta.module_name, tp.id), 'style':'padding-top:6px;', 'o_id':tp.id, 'o_model': tp._meta.module_name}})
            ret.append({'data':'%s <a onclick="abre_fecha(\'%s-%s\', \'blocos\'); return false;" id="a-%s-%s" style="color:#0000aa;">Abrir tudo</a>' % (tp.__unicode__(), tp._meta.module_name, tp.id, tp._meta.module_name, tp.id), 'attr':{'id':'%s-%s' % (tp._meta.module_name, tp.id), 'style':'padding-top:6px;', 'o_id':tp.id, 'o_model': tp._meta.module_name}})

    retorno_json = json.dumps(ret)
    return HttpResponse(retorno_json, content_type="application/json")


"""
Retorna os dados de um Historico Atual dado o ID de um patrimonio
"""
@login_required
@require_safe
def ajax_patrimonio_historico(request):
    retorno = {}
    patr_id = request.GET.get('id')
    patr = Patrimonio.objects.get(id=patr_id)
    historico = patr.historico_atual
    
    retorno = {'entidade_id':historico.endereco.endereco.entidade_id if historico.endereco.endereco_id else '',
               'entidade_desc':historico.endereco.endereco.entidade.__unicode__() if historico.endereco.endereco_id and historico.endereco.endereco.entidade_id else '',
               'localizacao_id':historico.endereco_id,
               'localizacao_desc':historico.endereco.__unicode__(),
               'posicao':historico.posicao,
               'descricao':historico.descricao,
               'data':str(datetime.date.today()),
               'estado_id':historico.estado_id,
               'estado_desc':historico.estado.__unicode__(),
               'memorando_id':historico.memorando_id,
               'memorando_desc': historico.memorando.__unicode__() if historico.memorando_id else '',
               }

    retorno_json = json.dumps(retorno)
    return HttpResponse(retorno_json, content_type='application/json')
