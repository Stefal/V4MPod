# coding: utf8
#!/usr/bin/env python

from  opv_api_client import RestClient, Filter, ressources

c = RestClient("http://opv_master:5000")

def get_untiled_lot(id_campaign, id_malette=42):
    
    lotlist = c.make(ressources.Campaign, id_campaign, id_malette).lots
    untiled_lots = []
    for lot in lotlist:
        if lot.tile is None:
            untiled_lots.append(lot.id_lot)
            
    return untiled_lots
    
