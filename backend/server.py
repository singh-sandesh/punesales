from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from typing import Optional
from pathlib import Path
from datetime import datetime, timezone
import os, uuid

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')
client = AsyncIOMotorClient(os.environ['MONGO_URL'])
db = client[os.environ['DB_NAME']]
app = FastAPI(title='VoltPulse Stock API')
api = APIRouter(prefix='/api')

class MasterIn(BaseModel):
    name: str
    code: Optional[str] = ''
    details: Optional[dict] = {}

class ProductIn(BaseModel):
    name: str
    brand_id: str
    model: str = ''
    capacity: str = ''
    battery_type: str = 'Tubular'
    purchase_rate: float = 0
    selling_rate: float = 0
    reorder_level: int = 10

class ItemIn(BaseModel):
    product_id: str
    quantity: int = Field(gt=0)
    rate: float = 0

class TransactionIn(BaseModel):
    kind: str
    party_id: Optional[str] = None
    warehouse_id: str
    reference: str = ''
    notes: str = ''
    items: list[ItemIn]

def now(): return datetime.now(timezone.utc).isoformat()
def clean(doc):
    if not doc: return None
    doc.pop('_id', None)
    return doc

async def seed():
    if await db.brands.count_documents({}): return
    brands = [{'id': str(uuid.uuid4()), 'name': n, 'code': c, 'active': True} for n,c in [('Exide','EXD'),('Massimo','MSM'),('Microtek','MTK')]]
    await db.brands.insert_many(brands)
    products=[]
    for b in brands:
        for cap in ['100Ah','120Ah','150Ah']:
            products.append({'id':str(uuid.uuid4()),'name':f"{b['name']} {cap} Tubular",'brand_id':b['id'],'model':f"{b['code']}-{cap[:-2]}",'capacity':cap,'battery_type':'Tubular','purchase_rate':8500 if cap=='150Ah' else 6800,'selling_rate':9800 if cap=='150Ah' else 7900,'reorder_level':20,'active':True})
    await db.products.insert_many(products)
    await db.suppliers.insert_many([{'id':str(uuid.uuid4()),'name':n,'active':True} for n in ['Powerline Distributors','Reliable Energy Supply','North Star Batteries']])
    await db.dealers.insert_many([{'id':str(uuid.uuid4()),'name':n,'phone':p,'city':c,'active':True} for n,p,c in [('ABC Batteries','9876543210','Pune'),('Shree Electricals','9822012345','Mumbai'),('Kiran Power House','9810012345','Nashik')]])
    warehouses=[{'id':str(uuid.uuid4()),'name':n,'active':True} for n in ['Main Warehouse','Pune Warehouse']]
    await db.warehouses.insert_many(warehouses)
    for i,p in enumerate(products): await db.inventory.insert_one({'id':str(uuid.uuid4()),'product_id':p['id'],'warehouse_id':warehouses[i%2]['id'],'available':35+(i%4)*12,'inward':70+(i%5)*10,'outward':25+(i%3)*5,'updated_at':now()})

@app.on_event('startup')
async def startup(): await seed()

@api.get('/bootstrap')
async def bootstrap():
    out={}
    for col in ['brands','products','suppliers','dealers','warehouses']:
        out[col]=[clean(x) for x in await db[col].find({}, {'_id':0}).to_list(2000)]
    return out

@api.get('/dashboard')
async def dashboard():
    inv=await db.inventory.find({}, {'_id':0}).to_list(5000)
    tx=await db.transactions.find({}, {'_id':0}).sort('created_at',-1).to_list(20)
    products={x['id']:x for x in await db.products.find({}, {'_id':0}).to_list(5000)}
    value=sum(x.get('available',0)*products.get(x.get('product_id'),{}).get('purchase_rate',0) for x in inv)
    return {'available':sum(x.get('available',0) for x in inv),'inward':sum(x.get('inward',0) for x in inv),'outward':sum(x.get('outward',0) for x in inv),'inventory_value':value,'transactions':tx}

@api.get('/stock')
async def stock():
    rows=await db.inventory.find({}, {'_id':0}).to_list(5000)
    products={x['id']:x for x in await db.products.find({}, {'_id':0}).to_list(5000)}
    brands={x['id']:x for x in await db.brands.find({}, {'_id':0}).to_list(5000)}
    warehouses={x['id']:x for x in await db.warehouses.find({}, {'_id':0}).to_list(100)}
    result=[]
    for r in rows:
        p=products.get(r['product_id'],{}); b=brands.get(p.get('brand_id'),{})
        result.append({**r,'product':p.get('name','Unknown'),'model':p.get('model',''),'brand':b.get('name','Unknown'),'warehouse':warehouses.get(r['warehouse_id'],{}).get('name','Unknown'),'value':r.get('available',0)*p.get('purchase_rate',0),'low':r.get('available',0)<=p.get('reorder_level',10)})
    return result

@api.post('/masters/{kind}')
async def create_master(kind:str, data:MasterIn):
    if kind not in ['brands','suppliers','dealers','warehouses']: raise HTTPException(400,'Unsupported master')
    doc={'id':str(uuid.uuid4()),'name':data.name.strip(),'code':data.code,'active':True,'created_at':now(),**data.details}
    await db[kind].insert_one(doc); return clean(doc)

@api.post('/products')
async def create_product(data:ProductIn):
    doc={'id':str(uuid.uuid4()),**data.model_dump(),'active':True,'created_at':now()}; await db.products.insert_one(doc); return clean(doc)

@api.post('/transactions')
async def create_transaction(data:TransactionIn):
    if data.kind not in ['inward','outward']: raise HTTPException(400,'Invalid transaction type')
    total=sum(x.quantity*x.rate for x in data.items)
    if data.kind=='outward':
        for item in data.items:
            row=await db.inventory.find_one({'product_id':item.product_id,'warehouse_id':data.warehouse_id},{'_id':0})
            if not row or row.get('available',0)<item.quantity: raise HTTPException(400,'Not enough available stock')
    tid=f"{'INW' if data.kind=='inward' else 'OUT'}-{(await db.transactions.count_documents({}))+1:06d}"
    doc={'id':str(uuid.uuid4()),'transaction_id':tid,'kind':data.kind,'party_id':data.party_id,'warehouse_id':data.warehouse_id,'reference':data.reference,'notes':data.notes,'items':[x.model_dump() for x in data.items],'total_quantity':sum(x.quantity for x in data.items),'total_value':total,'created_at':now(),'status':'posted'}
    await db.transactions.insert_one(doc)
    for item in data.items:
        delta=item.quantity if data.kind=='inward' else -item.quantity
        await db.inventory.update_one({'product_id':item.product_id,'warehouse_id':data.warehouse_id},{'$inc':{'available':delta,'inward':item.quantity if delta>0 else 0,'outward':item.quantity if delta<0 else 0},'$set':{'updated_at':now(),'rate':item.rate}} ,upsert=True)
    return clean(doc)

@api.get('/ledger')
async def ledger():
    tx=await db.transactions.find({}, {'_id':0}).sort('created_at',-1).to_list(500)
    return tx

app.include_router(api)
app.add_middleware(CORSMiddleware,allow_credentials=True,allow_origins=os.environ.get('CORS_ORIGINS','*').split(','),allow_methods=['*'],allow_headers=['*'])
@app.on_event('shutdown')
async def shutdown(): client.close()