# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2009 SISTHEO - eric@everlibre.fr
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import time
from osv import osv, fields
# 
# moves_form = '''<?xml version="1.0"?>
# <form string="Select move">
#     <field name="move_id"  on_change="onchange_move_id(move_id)" colspan="4"/>
#     <field name="journal_id" colspan="4"/>
#     <field name="period_id" colspan="4"/>
# </form>'''
# 
# moves_fields = {
#     'move_id': {'string': 'Modfication move', 'type': 'many2one', 'relation': 'account.move', 'required': True},
#     'journal_id': {'string': 'Journal', 'type': 'many2one', 'relation': 'account.journal', 'required': True},
#     'period_id': {'string': 'Period', 'type': 'many2one', 'relation': 'account.period', 'required': True},
# }
# def utf(val):
#         if isinstance(val, str):
#              str_utf8 = val
#         elif isinstance(val, unicode):
#              str_utf8 = val.encode('utf-8')
#         else:
#              str_utf8 = str(val)
#         return str_utf8
 
class update_account_move(osv.osv_memory):
    _name = "update.account.move"
    
    _columns = {
                  'move_id': fields.many2one('account.move','Modfication move'),
                  'journal_id': fields.many2one('account.journal','Journal'),
                  'period_id': fields.many2one('account.period','Period'), 
                  'date': fields.date('Date'), 
            }                                                     
    def _default_move(self,cr, uid, context, **kwargs):
        if 'move_id' in context:
            return context['move_id']
        if 'move_line_id' in context:
            move_line = self.pool.get('account.move.line').read(cr,uid, context['move_line_id'],['move_id'])
            return move_line['move_id'][0]
        return False 
    
    def onchange_move_id(self, cr, uid, ids, move_id):
        if move_id:
            result = {'value':{}} 
            move = self.pool.get('account.move').read(cr,uid,move_id,['journal_id','date','period_id'])
            result['value']['journal_id'] = move['journal_id'][0]
            result['value']['period_id'] = move['period_id'][0]
            result['value']['date'] = move['date']
            return result
   
    
    def annule_move(self,cr,uid,data,move):
        line_ids = self.pool.get('account.move.line').search(cr, uid, [('move_id', '=', data.move_id.id)])
        move_canceled = {}
        move_canceled['name'] = u"Annulation de l'écriture n°"+move['name']
        move_canceled['period_id'] = move.period_id.id
        move_canceled['journal_id'] = move.journal_id.id
        move_canceled['type'] = move.type
        move_canceled['ref'] = move.ref
        move_canceled['state'] = 'draft'
        move_canceled['date'] = move.date
        move_id = self.pool.get('account.move').create(cr, uid, move_canceled)
        for line_id in line_ids: 
             lineextourne={}
             line = self.pool.get('account.move.line').read(cr,uid,line_id)
             lineextourne['date'] = move_canceled['date']
             lineextourne['period_id'] = move.period_id.id
             lineextourne['journal_id'] = move.journal_id.id
             for elt in line:
                 if type(line[elt]) == type(tuple()):
                     lineextourne[elt]=line[elt][0]
                 else:
                     lineextourne[elt] = line[elt]
             lineextourne['debit'] = 0.0
             lineextourne['credit'] = 0.0
             lineextourne.pop('reconcile_id')
             lineextourne['debit'] = line['credit']
             lineextourne['credit'] = line['debit']
             if line['amount_currency']:
                 lineextourne['amount_currency'] = -line['amount_currency']
             lineextourne['move_id'] = move_id
             lineextourne.pop('id')
             self.pool.get('account.move.line').create(cr,uid,lineextourne)
        return move_id
    
    def cancel_move(self,cr,uid,ids,context):
 
        data = self.browse(cr,uid, ids[0])
        move = self.pool.get('account.move').browse(cr, uid, data.move_id.id)
        move_id = self.annule_move(cr, uid, data, move)
        
        return {
                'domain': "[('id','in', ["+str(move_id)+"])]",
                'name': 'Canceled move',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'account.move',
                'view_id': False,
                'type': 'ir.actions.act_window'
        }
        
        
    def move_move(self,cr,uid,ids,context):
        
        data = self.browse(cr,uid, ids[0])
        company_id =  self.pool.get('res.company').search(cr, uid, [('parent_id', '=', False)])[0]
        company =  self.pool.get('res.company').browse(cr, uid, company_id)
        res_company = company.currency_id.id
        currency_obj = self.pool.get('res.currency')
        move_ids = [data.move_id.id]
        move = self.pool.get('account.move').browse(cr, uid, data.move_id.id)
        cancel_move_id = self.annule_move(cr, uid, data, move)
        move_ids.append(cancel_move_id)
        new_move = {}
        new_move['name'] = move['name']
        new_move['period_id'] = data.period_id.id
        new_move['journal_id'] = data.journal_id.id
        new_move['type'] = move.type
        new_move['ref'] = move.ref
        new_move['state'] = 'draft'
        new_move['date'] = data.date
        line_ids = self.pool.get('account.move.line').search(cr, uid, [('move_id', '=', data.move_id.id)])
        move_id = self.pool.get('account.move').create(cr, uid, new_move)
        move_ids.append(move_id)
        for line_id in line_ids: 
             lineextourne={}
             line = self.pool.get('account.move.line').read(cr,uid,line_id)
             for elt in line:
                 if type(line[elt]) == type(tuple()):
                     lineextourne[elt]=line[elt][0]
                 else:
                     lineextourne[elt] = line[elt]
             
             lineextourne['date'] = new_move['date']
             lineextourne['period_id'] = data.period_id.id
             lineextourne['journal_id'] = data.journal_id.id
             lineextourne.pop('reconcile_id')
             lineextourne['move_id'] = move_id
             if line['amount_currency']:
                if data.period_id.id != move.period_id.id:
                    lineextourne['amount_currency']= currency_obj.compute(cr,uid,   res_company, lineextourne['currency_id'],lineextourne['debit'] - lineextourne['credit'] , context={'date':lineextourne['date']} )
                else:
                    lineextourne['amount_currency'] = line['amount_currency']
             lineextourne.pop('id')
             self.pool.get('account.move.line').create(cr,uid,lineextourne)
        return {
                'domain': "[('move_id','in',"+ str(move_ids)+")]",
                'name': 'Moved move',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'account.move.line',
                'view_id': False,
                'type': 'ir.actions.act_window'
        }
        
    def inverse_move(self,cr,uid,ids,context):
        data = self.browse(cr,uid, ids[0])
        company_id =  self.pool.get('res.company').search(cr, uid, [('parent_id', '=', False)])[0]
        company =  self.pool.get('res.company').browse(cr, uid, company_id)
        res_company = company.currency_id.id
        currency_obj = self.pool.get('res.currency')
        move_ids = [data.move_id.id]
        
        move = self.pool.get('account.move').browse(cr, uid, data.move_id.id)
        cancel_move_id = self.annule_move(cr, uid, data, move)
        move_ids.append(cancel_move_id)
        new_move = {}
        new_move['name'] = move['name']
        new_move['period_id'] = data.period_id.id
        new_move['journal_id'] = data.journal_id.id
        new_move['type'] = move.type
        new_move['ref'] = move.ref
        new_move['state'] = 'draft'
        new_move['date'] = data.date
        line_ids = self.pool.get('account.move.line').search(cr, uid, [('move_id', '=', data.move_id.id)])
        move_id = self.pool.get('account.move').create(cr, uid, new_move)
        move_ids.append(move_id)
        for line_id in line_ids: 
             lineextourne={}
             line = self.pool.get('account.move.line').read(cr,uid,line_id)
             for elt in line:
                 if type(line[elt]) == type(tuple()):
                     lineextourne[elt]=line[elt][0]
                 else:
                     lineextourne[elt] = line[elt]
             lineextourne['date'] = new_move['date']
             lineextourne['period_id'] = data.period_id.id
             lineextourne['journal_id'] = data.journal_id.id
             lineextourne['debit'] = line['credit']
             lineextourne['credit'] = line['debit']
             if line['amount_currency']:
                if data.period_id.id != move.period_id.id:
                    lineextourne['amount_currency']= currency_obj.compute(cr,uid, res_company, lineextourne['currency_id'],lineextourne['debit'] - lineextourne['credit'] , context={'date':lineextourne['date']} )
                else:
                    lineextourne['amount_currency'] = -line['amount_currency']
             lineextourne.pop('reconcile_id')
             lineextourne['move_id'] = move_id
             lineextourne.pop('id')
 
             self.pool.get('account.move.line').create(cr,uid,lineextourne)
        return {
                'domain': "[('move_id','in',"+ str(move_ids)+")]",
                'name': 'Inversed Move',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'account.move.line',
                'view_id': False,
                'type': 'ir.actions.act_window'
        }
    _defaults = {
                 'move_id': _default_move,
                 }    
update_account_move()
