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

import wizard
import pooler
import base64
import time
import os
moves_form = '''<?xml version="1.0"?>
<form string="Select move">
    <field name="move_ids" colspan="4"/>
</form>'''

moves_fields = {
    'move_ids': {'string': 'Lignes à extourner', 'type': 'one2many', 'relation': 'account.move', 'required': True},
}
def utf(val):
        if isinstance(val, str):
             str_utf8 = val
        elif isinstance(val, unicode):
             str_utf8 = val.encode('utf-8')
        else:
             str_utf8 = str(val)
        return str_utf8

class wizard_report(wizard.interface):
    def _get_defaults(self, cr, uid, data, context):
        data['form']['move_ids']=tuple()
        for id in data['ids']:
            move_id=pooler.get_pool(cr.dbname).get('account.move.line').read(cr,uid,id)['move_id'][0]
            if not move_id  in  data['form']['move_ids']:
                if pooler.get_pool(cr.dbname).get('account.move').read(cr,uid,move_id)['state']=='posted':
                    data['form']['move_ids'] =data['form']['move_ids']+(move_id,)
        return data['form']

    def extourne(self,cr,uid,data,context):
        for move in data['form']['move_ids']:
            mvtextourne=move[2]
            mvtextourne['name']=u"contrepassation de l'écriture n°"+move[2]['name']
            mvtextourne['state']='draft'
            mvext=pooler.get_pool(cr.dbname).get('account.move').create(cr,uid,mvtextourne)
            line_ids=pooler.get_pool(cr.dbname).get('account.move.line').search(cr,uid,[('move_id','=',move[1])])
            lineextourne={}
            for line_id in line_ids:
                line=pooler.get_pool(cr.dbname).get('account.move.line').read(cr,uid,line_id)
                for elt in line:
                    if type(line[elt]) == type(tuple()):
                        lineextourne[elt]=line[elt][0]
                    else:
                        lineextourne[elt]=line[elt]

                lineextourne['debit']=0.0
                lineextourne['credit']=0.0
                lineextourne.pop('reconcile_id')
                lineextourne['debit']=line['credit']
                lineextourne['credit']=line['debit']
                lineextourne['move_id']=mvext
                lineextourne.pop('id')
                pooler.get_pool(cr.dbname).get('account.move.line').create(cr,uid,lineextourne)
        return {}
    states = {
        'init': {
            'actions': [_get_defaults],
            'result': {'type':'form', 'arch':moves_form, 'fields':moves_fields, 'state':[('end','Cancel'),('extourne','Extourne')]}
        },
        'extourne': {
            'actions': [extourne],
            'result': {'type':'state',  'state':'end'}
        }
    }
wizard_report('l10n.fr.extourne.extourne')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

