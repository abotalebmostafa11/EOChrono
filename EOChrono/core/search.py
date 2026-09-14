import requests
from .geometry import geometry_wgs84,geojson_geometry
CDSE='https://catalogue.dataspace.copernicus.eu/odata/v1/Products'
STAC='https://planetarycomputer.microsoft.com/api/stac/v1/search'

def _get_json(url,params=None,headers=None,timeout=120):
    r=requests.get(url,params=params,headers=headers or {},timeout=timeout); r.raise_for_status(); return r.json()

def _odata(url,params,headers,limit):
    rows=[]; skip=0
    while len(rows)<limit:
        p=dict(params); p['$top']=min(1000,limit-len(rows)); p['$skip']=skip
        d=_get_json(url,p,headers).get('value',[]); rows.extend(d)
        if len(d)<p['$top']: break
        skip+=len(d)
    return rows[:limit]

def cdse(collection,contains,start,end,layer,limit=1000,token=None):
    wkt=geometry_wgs84(layer).asWkt()
    filters=[f"Collection/Name eq '{collection}'",f"contains(Name,'{contains}')",f'ContentDate/Start ge {start}T00:00:00.000Z',f'ContentDate/Start lt {end}T23:59:59.999Z',f"OData.CSC.Intersects(area=geography'SRID=4326;{wkt}')"]
    return _odata(CDSE,{'$filter':' and '.join(filters),'$orderby':'ContentDate/Start asc'},{'Authorization':'Bearer '+token} if token else {},limit)

def stac(collections,start,end,layer,limit=1000,query=None):
    payload={'collections':collections,'datetime':f'{start}T00:00:00Z/{end}T23:59:59Z','intersects':geojson_geometry(layer),'limit':min(100,limit)}
    if query: payload['query']=query
    rows=[]; url=STAC; first=True
    while url and len(rows)<limit:
        if first:
            r=requests.post(url,json=payload,timeout=120); first=False
        else:r=requests.get(url,timeout=120)
        r.raise_for_status(); d=r.json(); rows.extend(d.get('features',[])); url=next((x.get('href') for x in d.get('links',[]) if x.get('rel')=='next'),None)
    return rows[:limit]
