# -*- coding: utf-8 -*-
from django.test import TestCase
from decimal import Decimal

from datetime import date, timedelta, datetime
from django.db import models
from outorga.models import Termo, Item, OrigemFapesp, Estado as EstadoOutorga, Categoria, Outorga, Modalidade, Natureza_gasto, \
                           Acordo, Contrato, OrdemDeServico, TipoContrato, ArquivoOS
from identificacao.models import Entidade, Contato, Identificacao, Endereco
from protocolo.models import Protocolo, ItemProtocolo, TipoDocumento, Origem, Estado as EstadoProtocolo
from financeiro.models import Pagamento, ExtratoCC, Estado as EstadoFinanceiro, TipoComprovante, Auditoria, \
                            TipoComprovanteFinanceiro, ExtratoFinanceiro, LocalizaPatrocinio, ExtratoPatrocinio



class ExtratoCCTest(TestCase):
    def setUp(self):
        #Cria Termo
        e, created = EstadoOutorga.objects.get_or_create(nome='Vigente')
        t, create = Termo.objects.get_or_create(ano=2008, processo=22222, digito=2, defaults={'inicio': date(2008,1,1), 'estado':e})
        #Cria Outorga
        c1, created = Categoria.objects.get_or_create(nome='Inicial')
        c2, created = Categoria.objects.get_or_create(nome='Aditivo')

        o1, created = Outorga.objects.get_or_create(termo=t, categoria=c1, data_solicitacao=date(2007,12,1), defaults={'termino': date(2008,12,31), 'data_presta_contas': date(2008,2,28)})
        o2, created = Outorga.objects.get_or_create(termo=t, categoria=c2, data_solicitacao=date(2008,4,1), defaults={'termino': date(2008,12,31), 'data_presta_contas': date(2008,2,28)})

        #Cria Natureza de gasto
        m1, created = Modalidade.objects.get_or_create(sigla='STB', defaults={'nome': 'Servicos de Terceiro no Brasil', 'moeda_nacional': True})
        m11, created = Modalidade.objects.get_or_create(sigla='STB1', defaults={'nome': 'Servicos de Terceiro no Brasil', 'moeda_nacional': True})
        m2, created = Modalidade.objects.get_or_create(sigla='STE', defaults={'nome': 'Servicos de Terceiro no Exterior', 'moeda_nacional': False})

        n1, created = Natureza_gasto.objects.get_or_create(modalidade=m1, termo=t, valor_concedido='1500000.00')
        n2, created = Natureza_gasto.objects.get_or_create(modalidade=m11, termo=t, valor_concedido='3000000.00')

        #Cria Item de Outorga
        ent1, created = Entidade.objects.get_or_create(sigla='GTECH', defaults={'nome': 'Granero Tech', 'cnpj': '00.000.000/0000-00', 'fisco': True, 'url': ''})
        ent2, created = Entidade.objects.get_or_create(sigla='SAC', defaults={'nome': 'SAC do Brasil', 'cnpj': '00.000.000/0000-00', 'fisco': True, 'url': ''})
        
        end1, created = Endereco.objects.get_or_create(entidade=ent1)
        end2, created = Endereco.objects.get_or_create(entidade=ent2)

        i1, created = Item.objects.get_or_create(entidade=ent1, natureza_gasto=n1, descricao='Armazenagem', defaults={'justificativa': 'Armazenagem de equipamentos', 'quantidade': 12, 'valor': 2500})
        i2, created = Item.objects.get_or_create(entidade=ent2, natureza_gasto=n2, descricao='Serviço de Conexão Internacional', defaults={'justificativa': 'Link Internacional', 'quantidade': 12, 'valor': 250000})

        #Cria Protocolo
        ep, created = EstadoProtocolo.objects.get_or_create(nome='Aprovado')
        td, created = TipoDocumento.objects.get_or_create(nome='Nota Fiscal')
        og, created = Origem.objects.get_or_create(nome='Motoboy')

        cot1, created = Contato.objects.get_or_create(primeiro_nome='Joao', defaults={'email': 'joao@joao.com.br', 'tel': ''})
        cot2, created = Contato.objects.get_or_create(primeiro_nome='Alex', defaults={'email': 'alex@alex.com.br', 'tel': ''})

        iden1, created = Identificacao.objects.get_or_create(endereco=end1, contato=cot1, defaults={'funcao': 'Tecnico', 'area': 'Estoque', 'ativo': True})
        iden2, created = Identificacao.objects.get_or_create(endereco=end2, contato=cot2, defaults={'funcao': 'Gerente', 'area': 'Redes', 'ativo': True})

        p1, created = Protocolo.objects.get_or_create(termo=t, identificacao=iden1, tipo_documento=td, data_chegada=datetime(2008,9,30,10,10), defaults={'origem': og, 'estado': ep, 'num_documento': 8888, 'data_vencimento': date(2008,10,5), 'descricao': 'Conta mensal - armazenagem 09/2008', 'valor_total': None})
        p2, created = Protocolo.objects.get_or_create(termo=t, identificacao=iden2, tipo_documento=td, data_chegada=datetime(2008,9,30,10,11), defaults={'origem': og, 'estado': ep, 'num_documento': 7777, 'data_vencimento': date(2008,10,10), 'descricao': 'Serviço de Conexão Internacional - 09/2009', 'valor_total': None})

        #Criar Fonte Pagadora
        ef1, created = EstadoOutorga.objects.get_or_create(nome='Aprovado')

        ex1, created = ExtratoCC.objects.get_or_create(data_extrato=date(2008,10,30), data_oper=date(2008,10,5), cod_oper=333333, valor='2650', historico='TED')
        ex2, created = ExtratoCC.objects.get_or_create(data_extrato=date(2008,10,30), data_oper=date(2008,10,1), cod_oper=4444, valor='250000', historico='TED')

        a1, created = Acordo.objects.get_or_create(estado=ef1, descricao='Acordo entre Instituto UNIEMP e GTech')
        a2, created = Acordo.objects.get_or_create(estado=ef1, descricao='Acordo entre Instituto UNIEMP e SAC')
        a3, created = Acordo.objects.get_or_create(estado=ef1, descricao='Acordo entre Instituto UNIEMP e Terremark')

        of1, created = OrigemFapesp.objects.get_or_create(acordo=a1, item_outorga=i1)
        of2, created = OrigemFapesp.objects.get_or_create(acordo=a2, item_outorga=i2)

        fp1 = Pagamento(protocolo=p1, conta_corrente=ex1, origem_fapesp=of1, valor_fapesp='2650')
        fp1.save()
        fp2 = Pagamento(protocolo=p2, conta_corrente=ex2, origem_fapesp=of2, valor_fapesp='250000')
        fp2.save()
        
        efi1 = EstadoFinanceiro(nome="Estado financeiro 1")
        efi1.save()
        tcomprov1 = TipoComprovante(nome="Tipo Comprovante 1")
        tcomprov1.save()

        audit1 = Auditoria(estado=efi1, pagamento=fp1, tipo=tcomprov1, parcial=101.0, pagina=102.0, obs='observacao')
        audit1.save()

    def test_unicode(self):
        extrato = ExtratoCC.objects.get(pk=1)
        self.assertEquals(extrato.__unicode__(), u'2008-10-05 - 333333 - TED - 2650')
        
    def test_saldo(self):
        extrato = ExtratoCC.objects.get(pk=1)
        self.assertEquals(extrato.saldo, Decimal('252650.00'))
        
    def test_saldo_anterior(self):
        extrato = ExtratoCC.objects.get(pk=1)
        self.assertEquals(extrato.saldo_anterior, Decimal('250000.00'))
        
    def test_parciais(self):
        extrato = ExtratoCC.objects.get(pk=1)
        self.assertEquals(extrato.parciais(), u'STB [parcial 101 (102)]  ')
        
        

class TipoComprovanteFinanceiroTest(TestCase):
    def setUp(self):
        tcomprov1 = TipoComprovante(nome="Tipo Comprovante 1")
        tcomprov1.save()

    def test_unicode(self):
        tipo = TipoComprovante.objects.get(pk=1)
        self.assertEquals(tipo.__unicode__(), u'Tipo Comprovante 1')
        

class ExtratoFinanceiroTest(TestCase):
    def setUp(self):
        #Cria Termo
        e, created = EstadoOutorga.objects.get_or_create(nome='Vigente')
        t, create = Termo.objects.get_or_create(ano=2008, processo=22222, digito=2, defaults={'inicio': date(2008,1,1), 'estado':e})

        tcomprov1 = TipoComprovanteFinanceiro(nome="Tipo Comprovante Financeiro 1")
        tcomprov1.save()
        
        exf1 = ExtratoFinanceiro(termo=t, data_libera='2013-08-10', cod='EFC', historico="historico", valor=123456, tipo_comprovante=tcomprov1, parcial=543)
        exf1.save()
  

    def test_unicode(self):
        exf = ExtratoFinanceiro.objects.get(pk=1)
        self.assertEquals(exf.__unicode__(), u'2013-08-10 - EFC - historico - 123456')
        
    def test_despesa_caixa_falso(self):
        exf = ExtratoFinanceiro.objects.get(pk=1)
        self.assertFalse(exf.despesa_caixa)
        
    def test_despesa_caixa(self):
        tcomprov1 = TipoComprovanteFinanceiro(pk=1)
        tcomprov1.nome = u'Despesa de caixa' 
        tcomprov1.save()
        
        exf = ExtratoFinanceiro.objects.get(pk=1)
        exf.tipo=tcomprov1
        exf.save()

        self.assertTrue(exf.despesa_caixa)



class PagamentoTest(TestCase):
    def setUp(self):
        #Cria Termo
        e, created = EstadoOutorga.objects.get_or_create(nome='Vigente')
        t, create = Termo.objects.get_or_create(ano=2008, processo=22222, digito=2, defaults={'inicio': date(2008,1,1), 'estado':e})
        #Cria Outorga
        c1, created = Categoria.objects.get_or_create(nome='Inicial')
        c2, created = Categoria.objects.get_or_create(nome='Aditivo')

        o1, created = Outorga.objects.get_or_create(termo=t, categoria=c1, data_solicitacao=date(2007,12,1), defaults={'termino': date(2008,12,31), 'data_presta_contas': date(2008,2,28)})
        o2, created = Outorga.objects.get_or_create(termo=t, categoria=c2, data_solicitacao=date(2008,4,1), defaults={'termino': date(2008,12,31), 'data_presta_contas': date(2008,2,28)})

        #Cria Natureza de gasto
        m1, created = Modalidade.objects.get_or_create(sigla='STB', defaults={'nome': 'Servicos de Terceiro no Brasil', 'moeda_nacional': True})
        m11, created = Modalidade.objects.get_or_create(sigla='STB1', defaults={'nome': 'Servicos de Terceiro no Brasil', 'moeda_nacional': True})
        m2, created = Modalidade.objects.get_or_create(sigla='STE', defaults={'nome': 'Servicos de Terceiro no Exterior', 'moeda_nacional': False})

        n1, created = Natureza_gasto.objects.get_or_create(modalidade=m1, termo=t, valor_concedido='1500000.00')
        n2, created = Natureza_gasto.objects.get_or_create(modalidade=m11, termo=t, valor_concedido='3000000.00')

        #Cria Item de Outorga
        ent1, created = Entidade.objects.get_or_create(sigla='GTECH', defaults={'nome': 'Granero Tech', 'cnpj': '00.000.000/0000-00', 'fisco': True, 'url': ''})
        ent2, created = Entidade.objects.get_or_create(sigla='SAC', defaults={'nome': 'SAC do Brasil', 'cnpj': '00.000.000/0000-00', 'fisco': True, 'url': ''})
        
        end1, created = Endereco.objects.get_or_create(entidade=ent1)
        end2, created = Endereco.objects.get_or_create(entidade=ent2)

        i1, created = Item.objects.get_or_create(entidade=ent1, natureza_gasto=n1, descricao='Armazenagem', defaults={'justificativa': 'Armazenagem de equipamentos', 'quantidade': 12, 'valor': 2500})
        i2, created = Item.objects.get_or_create(entidade=ent2, natureza_gasto=n2, descricao='Serviço de Conexão Internacional', defaults={'justificativa': 'Link Internacional', 'quantidade': 12, 'valor': 250000})

        #Cria Protocolo
        ep, created = EstadoProtocolo.objects.get_or_create(nome='Aprovado')
        td, created = TipoDocumento.objects.get_or_create(nome='Nota Fiscal')
        og, created = Origem.objects.get_or_create(nome='Motoboy')

        cot1, created = Contato.objects.get_or_create(primeiro_nome='Joao', defaults={'email': 'joao@joao.com.br', 'tel': ''})
        cot2, created = Contato.objects.get_or_create(primeiro_nome='Alex', defaults={'email': 'alex@alex.com.br', 'tel': ''})

        iden1, created = Identificacao.objects.get_or_create(endereco=end1, contato=cot1, defaults={'funcao': 'Tecnico', 'area': 'Estoque', 'ativo': True})
        iden2, created = Identificacao.objects.get_or_create(endereco=end2, contato=cot2, defaults={'funcao': 'Gerente', 'area': 'Redes', 'ativo': True})

        p1, created = Protocolo.objects.get_or_create(termo=t, identificacao=iden1, tipo_documento=td, data_chegada=datetime(2008,9,30,10,10), defaults={'origem': og, 'estado': ep, 'num_documento': 8888, 'data_vencimento': date(2008,10,5), 'descricao': 'Conta mensal - armazenagem 09/2008', 'valor_total': None})
        p2, created = Protocolo.objects.get_or_create(termo=t, identificacao=iden2, tipo_documento=td, data_chegada=datetime(2008,9,30,10,11), defaults={'origem': og, 'estado': ep, 'num_documento': 7777, 'data_vencimento': date(2008,10,10), 'descricao': 'Serviço de Conexão Internacional - 09/2009', 'valor_total': None})

        #Criar Fonte Pagadora
        ef1, created = EstadoOutorga.objects.get_or_create(nome='Aprovado')

        ex1, created = ExtratoCC.objects.get_or_create(data_extrato=date(2008,10,30), data_oper=date(2008,10,5), cod_oper=333333, valor='2650', historico='TED')
        ex2, created = ExtratoCC.objects.get_or_create(data_extrato=date(2008,10,30), data_oper=date(2008,10,1), cod_oper=4444, valor='250000', historico='TED')

        a1, created = Acordo.objects.get_or_create(estado=ef1, descricao='Acordo entre Instituto UNIEMP e GTech')
        a2, created = Acordo.objects.get_or_create(estado=ef1, descricao='Acordo entre Instituto UNIEMP e SAC')
        a3, created = Acordo.objects.get_or_create(estado=ef1, descricao='Acordo entre Instituto UNIEMP e Terremark')

        of1, created = OrigemFapesp.objects.get_or_create(acordo=a1, item_outorga=i1)
        of2, created = OrigemFapesp.objects.get_or_create(acordo=a2, item_outorga=i2)

        fp1 = Pagamento(protocolo=p1, conta_corrente=ex1, origem_fapesp=of1, valor_fapesp='2650')
        fp1.save()
        fp2 = Pagamento(protocolo=p2, conta_corrente=ex2, origem_fapesp=of2, valor_fapesp='250000')
        fp2.save()
          

    def test_unicode(self):
        exf = Pagamento.objects.get(pk=1)
        self.assertEquals(exf.__unicode__(), u'8888 - 2650 - STB    ID: 1')
    
    def test_unicode_com_patrocinio(self):
        exf = Pagamento.objects.get(pk=1)
        exf.valor_patrocinio = 1234
        
        self.assertEquals(exf.__unicode__(), u'8888 - 3884 - STB    ID: 1')

    def test_unicode_com_auditoria(self):
        exf = Pagamento.objects.get(pk=1)

        efi1 = EstadoFinanceiro(nome="Estado financeiro 1")
        efi1.save()
        tcomprov1 = TipoComprovante(nome="Tipo Comprovante 1")
        tcomprov1.save()

        audit1 = Auditoria(estado=efi1, pagamento=exf, tipo=tcomprov1, parcial=101.0, pagina=102.0, obs='observacao')
        audit1.save()
        
        
        self.assertEquals(exf.__unicode__(), u'8888 - 2650 - STB, parcial 101, página 102    ID: 1')


    def test_unicode_para_auditoria(self):
        exf = Pagamento.objects.get(pk=1)

        efi1 = EstadoFinanceiro(nome="Estado financeiro 1")
        efi1.save()
        tcomprov1 = TipoComprovante(nome="Tipo Comprovante 1")
        tcomprov1.save()

        audit1 = Auditoria(estado=efi1, pagamento=exf, tipo=tcomprov1, parcial=101.0, pagina=102.0, obs='observacao')
        audit1.save()
        
        
        self.assertEquals(exf.unicode_para_auditoria(), u'8888 - 2650 - STB    ID: 1')

    def test_codigo_operacao(self):
        exf = Pagamento.objects.get(pk=1)
        self.assertEquals(exf.codigo_operacao(), 333333)

    def test_codigo_operacao_vazio(self):
        exf = Pagamento.objects.get(pk=1)
        exf.conta_corrente = None
        
        self.assertEquals(exf.codigo_operacao(), '')

    def test_anexos(self):
        exf = Pagamento.objects.get(pk=1)
        exf.conta_corrente = None
        
        self.assertEquals(exf.anexos(), u'Não')

    def test_anexos_com_auditoria(self):
        exf = Pagamento.objects.get(pk=1)
        exf.conta_corrente = None

        efi1 = EstadoFinanceiro(nome="Estado financeiro 1")
        efi1.save()
        tcomprov1 = TipoComprovante(nome="Tipo Comprovante 1")
        tcomprov1.save()

        audit1 = Auditoria(estado=efi1, pagamento=exf, tipo=tcomprov1, parcial=101.0, pagina=102.0, obs='observacao')
        audit1.save()

        self.assertEquals(exf.anexos(), u'Sim')

    def test_termo(self):
        exf = Pagamento.objects.get(pk=1)
        
        self.assertEquals(exf.termo(), u'08/22222-2')

    def test_item(self):
        exf = Pagamento.objects.get(pk=1)
        
        self.assertEquals(exf.item(), u'Armazenagem')

    def test_item_sem_origem_fapesp(self):
        exf = Pagamento.objects.get(pk=1)
        exf.origem_fapesp = None
        
        self.assertEquals(exf.item(), u'Não é Fapesp')

    def test_data(self):
        exf = Pagamento.objects.get(pk=1)
        
        self.assertEquals(exf.data(), date(2008,10,5))

    def test_nota(self):
        exf = Pagamento.objects.get(pk=1)
        
        self.assertEquals(exf.nota(), u'8888')

    def test_formata_valor_fapesp(self):
        exf = Pagamento.objects.get(pk=1)
        
        self.assertEquals(exf.formata_valor_fapesp(), u'R$ 2.650,00')

    def test_formata_valor_fapesp_dolar(self):
        exf = Pagamento.objects.get(pk=1)
        exf.origem_fapesp.item_outorga.natureza_gasto.modalidade.moeda_nacional = False
        
        self.assertEquals(exf.formata_valor_fapesp(), u'US$ 2.650,00')

    def test_pagina(self):
        exf = Pagamento.objects.get(pk=1)
        
        self.assertEquals(exf.pagina(), u'')

    def test_pagina_com_auditoria(self):
        exf = Pagamento.objects.get(pk=1)
        exf.conta_corrente = None

        efi1 = EstadoFinanceiro(nome="Estado financeiro 1")
        efi1.save()
        tcomprov1 = TipoComprovante(nome="Tipo Comprovante 1")
        tcomprov1.save()

        audit1 = Auditoria(estado=efi1, pagamento=exf, tipo=tcomprov1, parcial=101.0, pagina=102.0, obs='observacao')
        audit1.save()

        self.assertEquals(exf.pagina(), 102)

    def test_parcial(self):
        exf = Pagamento.objects.get(pk=1)
         
        self.assertEquals(exf.parcial(), u'')

    def test_parcial_com_auditoria(self):
        exf = Pagamento.objects.get(pk=1)
        exf.conta_corrente = None

        efi1 = EstadoFinanceiro(nome="Estado financeiro 1")
        efi1.save()
        tcomprov1 = TipoComprovante(nome="Tipo Comprovante 1")
        tcomprov1.save()

        audit1 = Auditoria(estado=efi1, pagamento=exf, tipo=tcomprov1, parcial=101.0, pagina=102.0, obs='observacao')
        audit1.save()

        self.assertEquals(exf.parcial(), 101)


class LocalizaPatrocinioTest(TestCase):
    def setUp(self):
        localiza, created = LocalizaPatrocinio.objects.get_or_create(consignado='Consignado')

    def test_unicode(self):
        localiza = LocalizaPatrocinio.objects.get(pk=1)
        self.assertEquals(localiza.__unicode__(), u'Consignado')



class ExtratoPatrocinioTest(TestCase):
    def setUp(self):
        localiza, created = LocalizaPatrocinio.objects.get_or_create(consignado='Consignado')
        extrato, created = ExtratoPatrocinio.objects.get_or_create(localiza=localiza, data_oper=date(2013, 02, 01), cod_oper=123, valor=1234.56, historico='Histórico', obs='Observação')

    def test_unicode(self):
        extrato = ExtratoPatrocinio.objects.get(pk=1)
        self.assertEquals(extrato.__unicode__(), u'Consignado - 2013-02-01 - 1234.56')


class EstadoTest(TestCase):
    def setUp(self):
        estado, created = EstadoFinanceiro .objects.get_or_create(nome='Estado Financeiro - nome')

    def test_unicode(self):
        estado = EstadoFinanceiro.objects.get(pk=1)
        self.assertEquals(estado.__unicode__(), u'Estado Financeiro - nome')


class AuditoriaTest(TestCase):
    def setUp(self):
        e, created = EstadoOutorga.objects.get_or_create(nome='Vigente')
        t, create = Termo.objects.get_or_create(ano=2008, processo=22222, digito=2, defaults={'inicio': date(2008,1,1), 'estado':e})
        #Cria Outorga
        c1, created = Categoria.objects.get_or_create(nome='Inicial')
        c2, created = Categoria.objects.get_or_create(nome='Aditivo')

        o1, created = Outorga.objects.get_or_create(termo=t, categoria=c1, data_solicitacao=date(2007,12,1), defaults={'termino': date(2008,12,31), 'data_presta_contas': date(2008,2,28)})
        o2, created = Outorga.objects.get_or_create(termo=t, categoria=c2, data_solicitacao=date(2008,4,1), defaults={'termino': date(2008,12,31), 'data_presta_contas': date(2008,2,28)})

        #Cria Natureza de gasto
        m1, created = Modalidade.objects.get_or_create(sigla='STB', defaults={'nome': 'Servicos de Terceiro no Brasil', 'moeda_nacional': True})
        m11, created = Modalidade.objects.get_or_create(sigla='STB1', defaults={'nome': 'Servicos de Terceiro no Brasil', 'moeda_nacional': True})
        m2, created = Modalidade.objects.get_or_create(sigla='STE', defaults={'nome': 'Servicos de Terceiro no Exterior', 'moeda_nacional': False})

        n1, created = Natureza_gasto.objects.get_or_create(modalidade=m1, termo=t, valor_concedido='1500000.00')
        n2, created = Natureza_gasto.objects.get_or_create(modalidade=m11, termo=t, valor_concedido='3000000.00')

        #Cria Item de Outorga
        ent1, created = Entidade.objects.get_or_create(sigla='GTECH', defaults={'nome': 'Granero Tech', 'cnpj': '00.000.000/0000-00', 'fisco': True, 'url': ''})
        ent2, created = Entidade.objects.get_or_create(sigla='SAC', defaults={'nome': 'SAC do Brasil', 'cnpj': '00.000.000/0000-00', 'fisco': True, 'url': ''})
        
        end1, created = Endereco.objects.get_or_create(entidade=ent1)
        end2, created = Endereco.objects.get_or_create(entidade=ent2)

        i1, created = Item.objects.get_or_create(entidade=ent1, natureza_gasto=n1, descricao='Armazenagem', defaults={'justificativa': 'Armazenagem de equipamentos', 'quantidade': 12, 'valor': 2500})
        i2, created = Item.objects.get_or_create(entidade=ent2, natureza_gasto=n2, descricao='Serviço de Conexão Internacional', defaults={'justificativa': 'Link Internacional', 'quantidade': 12, 'valor': 250000})

        #Cria Protocolo
        ep, created = EstadoProtocolo.objects.get_or_create(nome='Aprovado')
        td, created = TipoDocumento.objects.get_or_create(nome='Nota Fiscal')
        og, created = Origem.objects.get_or_create(nome='Motoboy')

        cot1, created = Contato.objects.get_or_create(primeiro_nome='Joao', defaults={'email': 'joao@joao.com.br', 'tel': ''})
        cot2, created = Contato.objects.get_or_create(primeiro_nome='Alex', defaults={'email': 'alex@alex.com.br', 'tel': ''})

        iden1, created = Identificacao.objects.get_or_create(endereco=end1, contato=cot1, defaults={'funcao': 'Tecnico', 'area': 'Estoque', 'ativo': True})
        iden2, created = Identificacao.objects.get_or_create(endereco=end2, contato=cot2, defaults={'funcao': 'Gerente', 'area': 'Redes', 'ativo': True})

        p1, created = Protocolo.objects.get_or_create(termo=t, identificacao=iden1, tipo_documento=td, data_chegada=datetime(2008,9,30,10,10), defaults={'origem': og, 'estado': ep, 'num_documento': 8888, 'data_vencimento': date(2008,10,5), 'descricao': 'Conta mensal - armazenagem 09/2008', 'valor_total': None})
        p2, created = Protocolo.objects.get_or_create(termo=t, identificacao=iden2, tipo_documento=td, data_chegada=datetime(2008,9,30,10,11), defaults={'origem': og, 'estado': ep, 'num_documento': 7777, 'data_vencimento': date(2008,10,10), 'descricao': 'Serviço de Conexão Internacional - 09/2009', 'valor_total': None})

        #Criar Fonte Pagadora
        ef1, created = EstadoOutorga.objects.get_or_create(nome='Aprovado')

        ex1, created = ExtratoCC.objects.get_or_create(data_extrato=date(2008,10,30), data_oper=date(2008,10,5), cod_oper=333333, valor='2650', historico='TED')
        ex2, created = ExtratoCC.objects.get_or_create(data_extrato=date(2008,10,30), data_oper=date(2008,10,1), cod_oper=4444, valor='250000', historico='TED')

        a1, created = Acordo.objects.get_or_create(estado=ef1, descricao='Acordo entre Instituto UNIEMP e GTech')
        a2, created = Acordo.objects.get_or_create(estado=ef1, descricao='Acordo entre Instituto UNIEMP e SAC')

        of1, created = OrigemFapesp.objects.get_or_create(acordo=a1, item_outorga=i1)
        of2, created = OrigemFapesp.objects.get_or_create(acordo=a2, item_outorga=i2)

        fp1 = Pagamento(protocolo=p1, conta_corrente=ex1, origem_fapesp=of1, valor_fapesp='2650')
        fp1.save()
        fp2 = Pagamento(protocolo=p2, conta_corrente=ex2, origem_fapesp=of2, valor_fapesp='250000')
        fp2.save()
        
        efi1 = EstadoFinanceiro(nome="Estado financeiro 1")
        efi1.save()
        tcomprov1 = TipoComprovante(nome="Tipo Comprovante 1")
        tcomprov1.save()

        audit1 = Auditoria(estado=efi1, pagamento=fp1, tipo=tcomprov1, parcial=101.0, pagina=102.0, obs='observacao')
        audit1.save()

    def test_unicode(self):
        audit1 = Auditoria.objects.get(pk=1)
        self.assertEquals(audit1.__unicode__(), u'Parcial: 101, página: 102')


class TipoComprovanteTest(TestCase):
    def setUp(self):
        tcomprov1 = TipoComprovante(nome="Tipo Comprovante 1")
        tcomprov1.save()

    def test_unicode(self):
        tcomprov1 = TipoComprovante.objects.get(pk=1)
        self.assertEquals(tcomprov1.__unicode__(), u'Tipo Comprovante 1')
