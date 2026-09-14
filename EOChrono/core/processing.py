from pathlib import Path
import re

INDEX_FORMULAS={
    'NDVI':'(NIR-RED)/(NIR+RED)', 'NDWI':'(GREEN-NIR)/(GREEN+NIR)',
    'MNDWI':'(GREEN-SWIR1)/(GREEN+SWIR1)', 'NDMI':'(NIR-SWIR1)/(NIR+SWIR1)',
    'NDBI':'(SWIR1-NIR)/(SWIR1+NIR)', 'SAVI':'1.5*((NIR-RED)/(NIR+RED+0.5))',
    'BSI':'((SWIR1+RED)-(NIR+BLUE))/((SWIR1+RED)+(NIR+BLUE))',
    'EVI':'2.5*((NIR-RED)/(NIR+6*RED-7.5*BLUE+1))'
}
ALIASES={
    'BLUE':['B02','B2','SR_B2','BAND2'], 'GREEN':['B03','B3','SR_B3','BAND3'],
    'RED':['B04','B4','SR_B4','BAND4'], 'NIR':['B08','B8','SR_B5','BAND5'],
    'SWIR1':['B11','B6','SR_B6','BAND6']
}

def find_band(folder, aliases):
    candidates=[]
    for p in Path(folder).rglob('*'):
        if p.suffix.lower() not in ('.tif','.tiff','.vrt'): continue
        n=p.stem.upper()
        if any(re.search(rf'(^|[_\-.]){re.escape(a)}([_\-.]|$)',n) for a in aliases): candidates.append(p)
    return sorted(candidates, key=lambda x: len(x.name))[0] if candidates else None

def calculate_index(folder,name,output=None):
    if name not in INDEX_FORMULAS: raise ValueError(f'Unsupported index: {name}')
    from qgis import processing
    need={
      'NDVI':['NIR','RED'],'NDWI':['GREEN','NIR'],'MNDWI':['GREEN','SWIR1'],'NDMI':['NIR','SWIR1'],
      'NDBI':['SWIR1','NIR'],'SAVI':['NIR','RED'],'BSI':['SWIR1','RED','NIR','BLUE'],'EVI':['NIR','RED','BLUE']
    }[name]
    bands={k:find_band(folder,ALIASES[k]) for k in need}
    missing=[k for k,v in bands.items() if not v]
    if missing: raise RuntimeError('Missing bands: '+', '.join(missing))
    # Use QGIS raster calculator with named temporary layer references.
    layers=[]; expr=INDEX_FORMULAS[name]
    for i,(k,p) in enumerate(bands.items()):
        from qgis.core import QgsRasterLayer
        layer=QgsRasterLayer(str(p),p.stem)
        if not layer.isValid(): raise RuntimeError(f'Invalid raster: {p}')
        layers.append(layer); expr=expr.replace(k,f'"{layer.name()}@1"')
    out=Path(output or Path(folder)/(name+'.tif')); out.parent.mkdir(parents=True,exist_ok=True)
    processing.run('native:rastercalc',{'LAYERS':layers,'EXPRESSION':expr,'CRS':layers[0].crs(),'EXTENT':layers[0].extent(),'CELL_SIZE':layers[0].rasterUnitsPerPixelX(),'OUTPUT':str(out)})
    return out

def clip_raster(input_path,aoi_path,output_path):
    from qgis import processing
    return processing.run('gdal:cliprasterbymasklayer',{'INPUT':str(input_path),'MASK':str(aoi_path),'CROP_TO_CUTLINE':True,'KEEP_RESOLUTION':True,'OUTPUT':str(output_path)})['OUTPUT']

def reproject_raster(input_path,output_path,crs):
    from qgis import processing
    return processing.run('gdal:warpreproject',{'INPUT':str(input_path),'TARGET_CRS':crs,'OUTPUT':str(output_path)})['OUTPUT']

def mosaic_rasters(inputs,output_path):
    from qgis import processing
    return processing.run('gdal:merge',{'INPUT':[str(x) for x in inputs],'OUTPUT':str(output_path),'SEPARATE':False})['OUTPUT']

def add_raster(path,name=None):
    from qgis.core import QgsProject,QgsRasterLayer
    l=QgsRasterLayer(str(path),name or Path(path).stem)
    if l.isValid(): QgsProject.instance().addMapLayer(l); return l
    return None


def batch_calculate_index(folders,name,output_root):
    root=Path(output_root); root.mkdir(parents=True,exist_ok=True); outputs=[]
    for folder in folders:
        folder=Path(folder)
        try: outputs.append(calculate_index(folder,name,root/(folder.name+'_'+name+'.tif')))
        except Exception as e: outputs.append({'folder':str(folder),'error':str(e)})
    return outputs

def raster_info(path):
    from qgis.core import QgsRasterLayer
    layer=QgsRasterLayer(str(path),Path(path).stem)
    if not layer.isValid(): raise RuntimeError(f'Invalid raster: {path}')
    return {'name':layer.name(),'crs':layer.crs().authid(),'width':layer.width(),'height':layer.height(),'bands':layer.bandCount(),'pixel_x':layer.rasterUnitsPerPixelX(),'pixel_y':layer.rasterUnitsPerPixelY(),'extent':layer.extent().toString()}
