from .search import cdse,stac
CFG={
 'Sentinel-1':{'type':'cdse','collection':'SENTINEL-1','contains':'IW_GRDH_1S'},
 'Sentinel-2':{'type':'cdse','collection':'SENTINEL-2','contains':'MSIL2A'},
 'Landsat-7':{'type':'stac','collections':['landsat-c2-l2'],'platform':'landsat-7'},
 'Landsat-8':{'type':'stac','collections':['landsat-c2-l2'],'platform':'landsat-8'},
 'Landsat-9':{'type':'stac','collections':['landsat-c2-l2'],'platform':'landsat-9'},
 'MODIS-MOD09A1':{'type':'stac','collections':['modis-09A1-061'],'platform':None},
 'MODIS-MOD13Q1':{'type':'stac','collections':['modis-13Q1-061'],'platform':None},
 'MODIS-MOD11A2':{'type':'stac','collections':['modis-11A2-061'],'platform':None},
 'MODIS-MOD10A2':{'type':'stac','collections':['modis-10A2-061'],'platform':None},
}

def _cdse(p,name):
    a={x.get('Name'):x.get('Value') for x in p.get('Attributes',[])}; pid=p.get('Id'); d=p.get('ContentDate',{}).get('Start')
    return {'id':pid,'name':p.get('Name'),'date':d,'cloud':a.get('cloudCover'),'size':p.get('ContentLength'),'provider':name,'platform':name,'url':f'https://download.dataspace.copernicus.eu/odata/v1/Products({pid})/$value','assets':{},'attributes':a,'coverage':100,'asset_count':0}

def _stac_feature(f,name):
    pr=f.get('properties',{}); assets=f.get('assets',{})
    # Keep only direct downloadable assets and expose their role/title metadata.
    return {'id':f.get('id'),'name':f.get('id'),'date':pr.get('datetime') or pr.get('start_datetime'),'cloud':pr.get('eo:cloud_cover'),'size':None,'url':None,'assets':assets,'provider':name,'platform':pr.get('platform'),'bbox':f.get('bbox'),'properties':pr,'coverage':100,'asset_count':len(assets)}

def search_provider(name,start,end,layer,limit,token=None):
    c=CFG[name]
    if c['type']=='cdse': return [_cdse(p,name) for p in cdse(c['collection'],c['contains'],start,end,layer,limit,token)]
    out=[]
    for f in stac(c['collections'],start,end,layer,limit):
        pr=f.get('properties',{}); platform=str(pr.get('platform','')).lower()
        if c.get('platform') and platform!=c['platform']: continue
        out.append(_stac_feature(f,name))
    return out[:limit]
