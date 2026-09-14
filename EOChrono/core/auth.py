import requests
TOKEN_URL="https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
class CDSEAuth:
    def __init__(self): self.access_token=None; self.refresh_token=None
    def login(self,user,password):
        r=requests.post(TOKEN_URL,data={"client_id":"cdse-public","username":user,"password":password,"grant_type":"password"},timeout=60); r.raise_for_status(); d=r.json(); self.access_token=d["access_token"]; self.refresh_token=d.get("refresh_token"); return self.access_token
    def refresh(self):
        if not self.refresh_token: raise RuntimeError("No CDSE refresh token available")
        r=requests.post(TOKEN_URL,data={"client_id":"cdse-public","grant_type":"refresh_token","refresh_token":self.refresh_token},timeout=60); r.raise_for_status(); d=r.json(); self.access_token=d["access_token"]; self.refresh_token=d.get("refresh_token",self.refresh_token); return self.access_token
