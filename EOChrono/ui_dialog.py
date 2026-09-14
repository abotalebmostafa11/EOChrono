from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtCore import QDate,QThread,pyqtSignal,Qt
from qgis.core import QgsProject,QgsVectorLayer
from pathlib import Path
import json,re,concurrent.futures
from .core.auth import CDSEAuth
from .core.geometry import load_aoi
from .core.providers import CFG,search_provider
from .core.quality import dedupe,select_best,monthly_best,balanced_time_series,score,report
from .core.inventory import write_inventory,write_metadata
from .core.downloader import Downloader,DownloadCancelled
from .core.project import save_project,load_project
from .core.processing import INDEX_FORMULAS,calculate_index,add_raster,clip_raster,reproject_raster,mosaic_rasters

class SearchWorker(QThread):
    done=pyqtSignal(object); fail=pyqtSignal(str)
    def __init__(self,args): super().__init__(); self.args=args
    def run(self):
        try:self.done.emit(search_provider(*self.args))
        except Exception as e:self.fail.emit(str(e))

class DownloadWorker(QThread):
    progress=pyqtSignal(int,int,int); item=pyqtSignal(int,bool,str); done=pyqtSignal()
    def __init__(self,rows,out,token,resume,workers,verify):
        super().__init__(); self.rows=rows; self.out=Path(out); self.token=token; self.resume=resume; self.workers=max(1,workers); self.verify=verify; self.stop_flag=False
    def cancel(self): self.stop_flag=True
    def _asset(self,r):
        assets=r.get('assets') or {}
        preferred=['visual','rendered_preview','B08','B04','SR_B5','SR_B4','data']
        for k in preferred:
            a=assets.get(k)
            if isinstance(a,dict) and a.get('href'): return a['href'],k
        for k,a in assets.items():
            if isinstance(a,dict) and a.get('href'): return a['href'],k
        return r.get('url'),None
    def run_one(self,idx,r):
        if self.stop_flag:return idx,False,'Cancelled'
        url,asset=self._asset(r)
        if not url:return idx,False,'No downloadable asset found'
        name=re.sub(r'[<>:"/\\|?*]','_',r.get('name') or r.get('id') or f'item_{idx+1}')
        ext='.zip' if 'dataspace' in url or 'Products(' in url else Path(url.split('?')[0]).suffix or '.tif'
        dest=self.out/(name+ext)
        dl=Downloader({'Authorization':'Bearer '+self.token} if self.token else {})
        def pg(done,total):self.progress.emit(idx,done,total or 0)
        try:
            dl.download(url,dest,self.resume,pg,lambda:self.stop_flag)
            if self.verify and (not dest.exists() or dest.stat().st_size==0):raise RuntimeError('Downloaded file is empty')
            r.update({'status':'Downloaded','local_path':str(dest),'asset':asset})
            write_metadata(dest.with_suffix('.json'),r)
            return idx,True,str(dest)
        except DownloadCancelled:return idx,False,'Cancelled'
        except Exception as e:return idx,False,str(e)
    def run(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as ex:
            futs=[ex.submit(self.run_one,i,r) for i,r in enumerate(self.rows)]
            for fut in concurrent.futures.as_completed(futs):
                self.item.emit(*fut.result())
                if self.stop_flag: break
        self.done.emit()

class GeoImageDialog(QDialog):
    def __init__(self,iface,plugin_dir):
        super().__init__(iface.mainWindow()); self.iface=iface; self.plugin_dir=Path(plugin_dir); self.auth=CDSEAuth(); self.rows=[]; self.resize(1500,920); self.setWindowTitle('EOChrono 7.0.0 — Earth Observation Manager'); self.build()
    def build(self):
        root=QVBoxLayout(self); tabs=QTabWidget(); root.addWidget(tabs)
        w=QWidget(); f=QFormLayout(w)
        self.sat=QComboBox(); self.sat.addItems(CFG.keys()); f.addRow('Data source',self.sat)
        ao=QHBoxLayout(); self.aoi=QLineEdit(); b=QPushButton('Browse'); b.clicked.connect(self.browse_aoi); ao.addWidget(self.aoi); ao.addWidget(b); f.addRow('AOI',ao)
        dr=QHBoxLayout(); self.df=QDateEdit(QDate(2018,1,1)); self.dt=QDateEdit(QDate.currentDate()); [x.setCalendarPopup(True) for x in (self.df,self.dt)]; dr.addWidget(self.df); dr.addWidget(self.dt); f.addRow('Date range',dr)
        self.cloud=QDoubleSpinBox(); self.cloud.setRange(0,100); self.cloud.setValue(20); self.cloud.setSuffix(' %'); f.addRow('Max cloud',self.cloud)
        self.limit=QSpinBox(); self.limit.setRange(1,50000); self.limit.setValue(1000); f.addRow('Search limit',self.limit)
        self.monthly=QCheckBox('Best scene per month'); f.addRow('',self.monthly)
        self.ts_count=QSpinBox(); self.ts_count.setRange(1,10000); self.ts_count.setValue(12); f.addRow('Time-series target count',self.ts_count)
        self.rank=QComboBox(); self.rank.addItems(['Balanced','Lowest cloud','AOI coverage']); f.addRow('Ranking',self.rank)
        tabs.addTab(w,'01 Search')
        a=QWidget(); af=QFormLayout(a); self.user=QLineEdit(); self.pw=QLineEdit(); self.pw.setEchoMode(QLineEdit.Password); lb=QPushButton('Login / Refresh CDSE'); lb.clicked.connect(self.login); af.addRow('CDSE email',self.user); af.addRow('Password',self.pw); af.addRow('',lb); tabs.addTab(a,'02 Access')
        r=QWidget(); rl=QVBoxLayout(r); bar=QHBoxLayout()
        for text,fn in [('SEARCH',self.search),('SELECT BEST',self.select_best),('TIME SERIES',self.time_series),('SELECT ALL',self.select_all),('CLEAR',self.clear_checks),('QUALITY',self.show_report),('SAVE PROJECT',self.save_proj),('LOAD PROJECT',self.load_proj)]:
            q=QPushButton(text); q.clicked.connect(fn); bar.addWidget(q)
        rl.addLayout(bar); self.table=QTableWidget(0,11); self.table.setSelectionBehavior(QAbstractItemView.SelectRows); self.table.setHorizontalHeaderLabels(['Use','Date','Name','Provider','Cloud %','Status','Local path','Score','Asset','ID','Coverage %']); self.table.horizontalHeader().setStretchLastSection(True); rl.addWidget(self.table); tabs.addTab(r,'03 Scenes')
        d=QWidget(); df=QFormLayout(d); oo=QHBoxLayout(); self.out=QLineEdit(str(Path.home()/'EOChronoData')); ob=QPushButton('Output'); ob.clicked.connect(self.outdir); oo.addWidget(self.out); oo.addWidget(ob); df.addRow('Output',oo)
        self.workers=QSpinBox(); self.workers.setRange(1,12); self.workers.setValue(4); df.addRow('Concurrent downloads',self.workers)
        self.resume=QCheckBox('Resume interrupted files'); self.resume.setChecked(True); df.addRow('',self.resume); self.verify=QCheckBox('Validate output'); self.verify.setChecked(True); df.addRow('',self.verify)
        self.bestcount=QSpinBox(); self.bestcount.setRange(1,5000); self.bestcount.setValue(12); df.addRow('Best scenes count',self.bestcount)
        bb=QHBoxLayout(); x=QPushButton('DOWNLOAD SELECTED'); x.clicked.connect(self.download); self.cancelb=QPushButton('CANCEL'); self.cancelb.clicked.connect(self.cancel); bb.addWidget(x); bb.addWidget(self.cancelb); df.addRow('',bb); self.pb=QProgressBar(); df.addRow('Current item',self.pb); tabs.addTab(d,'04 Download')
        p=QWidget(); pf=QFormLayout(p); self.index=QComboBox(); self.index.addItems(['None']+list(INDEX_FORMULAS)); pf.addRow('Index',self.index); ib=QPushButton('Calculate index'); ib.clicked.connect(self.calc_index); pf.addRow('',ib)
        self.proc_input=QLineEdit(); pi=QPushButton('Input folder'); pi.clicked.connect(lambda:self.pick_folder(self.proc_input)); row=QHBoxLayout(); row.addWidget(self.proc_input); row.addWidget(pi); pf.addRow('Processing input',row)
        self.proc_out=QLineEdit(); po=QPushButton('Output folder'); po.clicked.connect(lambda:self.pick_folder(self.proc_out)); row=QHBoxLayout(); row.addWidget(self.proc_out); row.addWidget(po); pf.addRow('Processing output',row)
        cb=QHBoxLayout(); self.addmap=QCheckBox('Add result to QGIS'); self.addmap.setChecked(True); cb.addWidget(self.addmap); c=QPushButton('CLIP'); c.clicked.connect(self.do_clip); rp=QPushButton('REPROJECT'); rp.clicked.connect(self.do_reproject); mo=QPushButton('MOSAIC'); mo.clicked.connect(self.do_mosaic); cb.addWidget(c); cb.addWidget(rp); cb.addWidget(mo); pf.addRow('',cb); tabs.addTab(p,'05 Processing')
        self.status=QLabel('Ready — EOChrono 7.0.0'); root.addWidget(self.status)
    def pick_folder(self,target):
        p=QFileDialog.getExistingDirectory(self,'Select folder');
        if p:target.setText(p)
    def browse_aoi(self):
        p,_=QFileDialog.getOpenFileName(self,'AOI','','Vector (*.gpkg *.shp *.geojson *.json)');
        if p:self.aoi.setText(p)
    def outdir(self):
        p=QFileDialog.getExistingDirectory(self,'Output');
        if p:self.out.setText(p)
    def layer(self):
        p=self.aoi.text().strip()
        if p:return load_aoi(p)
        for l in QgsProject.instance().mapLayers().values():
            if isinstance(l,QgsVectorLayer) and l.isValid() and l.geometryType()==2:return l
        raise ValueError('Select a polygon AOI or browse to one')
    def login(self):
        try:self.auth.login(self.user.text().strip(),self.pw.text()); self.pw.clear(); self.status.setText('CDSE login successful')
        except Exception as e:QMessageBox.critical(self,'Login failed',str(e))
    def search(self):
        try:
            if self.sat.currentText().startswith('Sentinel') and not self.auth.access_token: raise RuntimeError('Login to Copernicus Data Space first')
            args=(self.sat.currentText(),self.df.date().toString('yyyy-MM-dd'),self.dt.date().toString('yyyy-MM-dd'),self.layer(),self.limit.value(),self.auth.access_token)
            self.status.setText('Searching...'); self.sw=SearchWorker(args); self.sw.done.connect(self.results); self.sw.fail.connect(lambda e:QMessageBox.critical(self,'Search error',e)); self.sw.start()
        except Exception as e:QMessageBox.critical(self,'Search error',str(e))
    def results(self,rows):
        rows=dedupe(rows); filtered=[]
        for r in rows:
            try: c=float(r.get('cloud')) if r.get('cloud') is not None else None
            except: c=None
            if c is None or c<=self.cloud.value():filtered.append(r)
        self.rows=filtered; mode={'Balanced':'balanced','Lowest cloud':'lowest_cloud','AOI coverage':'coverage'}[self.rank.currentText()]
        if self.monthly.isChecked():self.rows=monthly_best(self.rows,mode)
        for r in self.rows:r['score']=round(score(r,mode),2); r.setdefault('status','Ready')
        self.populate(); self.write_inv(); self.status.setText(f'Found {len(self.rows)} scenes')
    def populate(self):
        self.table.setRowCount(len(self.rows))
        for i,r in enumerate(self.rows):
            c=QTableWidgetItem(); c.setCheckState(Qt.Unchecked); self.table.setItem(i,0,c)
            vals=[r.get('date'),r.get('name'),r.get('provider'),r.get('cloud'),r.get('status','Ready'),r.get('local_path',''),r.get('score',''),r.get('asset',''),r.get('id',''),r.get('coverage',100)]
            for j,v in enumerate(vals,1):self.table.setItem(i,j,QTableWidgetItem('' if v is None else str(v)))
    def select_all(self):
        for i in range(self.table.rowCount()):self.table.item(i,0).setCheckState(Qt.Checked)
    def clear_checks(self):
        for i in range(self.table.rowCount()):self.table.item(i,0).setCheckState(Qt.Unchecked)
    def select_best(self):
        if not self.rows:return
        mode={'Balanced':'balanced','Lowest cloud':'lowest_cloud','AOI coverage':'coverage'}[self.rank.currentText()]; ids=select_best(self.rows,self.bestcount.value(),mode); self.clear_checks()
        for i in ids:self.table.item(i,0).setCheckState(Qt.Checked)
        self.status.setText(f'Selected {len(ids)} best scenes')
    def time_series(self):
        if not self.rows:return
        mode={'Balanced':'balanced','Lowest cloud':'lowest_cloud','AOI coverage':'coverage'}[self.rank.currentText()]; chosen=balanced_time_series(self.rows,self.ts_count.value(),mode); chosen_ids={id(x) for x in chosen}; self.clear_checks()
        for i,r in enumerate(self.rows):
            if id(r) in chosen_ids:self.table.item(i,0).setCheckState(Qt.Checked)
        self.status.setText(f'Time-series selected: {len(chosen)} scenes')
    def selected(self):return [r for i,r in enumerate(self.rows) if self.table.item(i,0).checkState()==Qt.Checked]
    def write_inv(self):
        try:write_inventory(Path(self.out.text())/self.sat.currentText().replace('-','_')/'inventory.csv',self.rows)
        except Exception:pass
    def download(self):
        rows=self.selected()
        if not rows:return QMessageBox.information(self,'Download','Select scenes first')
        out=Path(self.out.text())/self.sat.currentText().replace('-','_'); self.pb.setValue(0); self.status.setText(f'Downloading {len(rows)} scenes...'); self.dw=DownloadWorker(rows,out,self.auth.access_token,self.resume.isChecked(),self.workers.value(),self.verify.isChecked()); self.dw.item.connect(self.item); self.dw.progress.connect(self.progress); self.dw.done.connect(self.finished); self.dw.start()
    def progress(self,i,done,total):
        if total:self.pb.setValue(min(100,int(done*100/total)))
    def item(self,i,ok,msg):
        r=self.dw.rows[i]; r['status']='Downloaded' if ok else 'FAILED: '+msg; r['local_path']=msg if ok else ''; self.populate(); self.write_inv()
    def finished(self):self.pb.setValue(100 if not self.dw.stop_flag else 0); self.status.setText('Download queue finished')
    def cancel(self):
        if hasattr(self,'dw') and self.dw.isRunning():self.dw.cancel(); self.status.setText('Cancelling...')
    def show_report(self):QMessageBox.information(self,'Quality Report',json.dumps(report(self.rows),indent=2,ensure_ascii=False))
    def settings(self):return {'satellite':self.sat.currentText(),'start':self.df.date().toString('yyyy-MM-dd'),'end':self.dt.date().toString('yyyy-MM-dd'),'cloud':self.cloud.value(),'limit':self.limit.value(),'monthly':self.monthly.isChecked(),'ranking':self.rank.currentText(),'best_count':self.bestcount.value(),'ts_count':self.ts_count.value(),'output':self.out.text(),'workers':self.workers.value(),'resume':self.resume.isChecked(),'verify':self.verify.isChecked()}
    def save_proj(self):
        p,_=QFileDialog.getSaveFileName(self,'Save Project','','EOChrono Project (*.gip.json)');
        if p:save_project(p,self.settings(),self.rows); self.status.setText('Project saved')
    def load_proj(self):
        p,_=QFileDialog.getOpenFileName(self,'Load Project','','EOChrono Project (*.gip.json)');
        if not p:return
        try:
            s=load_project(p); idx=self.sat.findText(s['satellite']);
            if idx>=0:self.sat.setCurrentIndex(idx)
            self.df.setDate(QDate.fromString(s['start'],'yyyy-MM-dd')); self.dt.setDate(QDate.fromString(s['end'],'yyyy-MM-dd')); self.cloud.setValue(s['cloud']); self.limit.setValue(s['limit']); self.monthly.setChecked(s['monthly']); self.bestcount.setValue(s['best_count']); self.ts_count.setValue(s.get('ts_count',12)); self.out.setText(s['output']); self.workers.setValue(s.get('workers',4)); self.resume.setChecked(s.get('resume',True)); self.verify.setChecked(s.get('verify',True)); self.rows=s.get('rows',[]); self.populate(); self.status.setText('Project loaded')
        except Exception as e:QMessageBox.critical(self,'Load project',str(e))
    def calc_index(self):
        name=self.index.currentText(); folder=self.proc_input.text().strip() or self.out.text()
        if name=='None':return
        if not folder:return
        try:
            out=calculate_index(folder,name,self.proc_out.text().strip() or None)
            if self.addmap.isChecked():add_raster(out,name)
            QMessageBox.information(self,'Processing',f'{name} created:\n{out}')
        except Exception as e:QMessageBox.critical(self,'Processing error',str(e))
    def do_clip(self):
        inp=self.proc_input.text().strip(); out=self.proc_out.text().strip();
        if not inp or not out:return QMessageBox.warning(self,'Clip','Set input raster and output file/folder')
        try:
            src=next(Path(inp).rglob('*.tif')) if Path(inp).is_dir() else Path(inp); dst=Path(out) if Path(out).suffix else Path(out)/(src.stem+'_clip.tif'); result=clip_raster(src,self.aoi.text().strip(),dst); add_raster(result) if self.addmap.isChecked() else None
        except Exception as e:QMessageBox.critical(self,'Clip error',str(e))
    def do_reproject(self):
        inp=self.proc_input.text().strip(); out=self.proc_out.text().strip();
        if not inp or not out:return
        try:
            src=Path(inp); dst=Path(out) if Path(out).suffix else Path(out)/(src.stem+'_reprojected.tif'); result=reproject_raster(src,dst,'EPSG:4326'); add_raster(result) if self.addmap.isChecked() else None
        except Exception as e:QMessageBox.critical(self,'Reproject error',str(e))
    def do_mosaic(self):
        folder=self.proc_input.text().strip(); out=self.proc_out.text().strip();
        if not folder or not out:return
        try:
            files=list(Path(folder).glob('*.tif')); 
            if not files:raise RuntimeError('No TIFF files found')
            dst=Path(out) if Path(out).suffix else Path(out)/'mosaic.tif'; result=mosaic_rasters(files,dst); add_raster(result) if self.addmap.isChecked() else None
        except Exception as e:QMessageBox.critical(self,'Mosaic error',str(e))
