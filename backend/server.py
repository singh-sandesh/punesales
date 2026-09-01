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
app = FastAPI(title='PSC Stock API')
api = APIRouter(prefix='/api')
MAIN_LOCATION = 'main-stock'
PRODUCT_TYPES = {'battery', 'inverter', 'trolley'}


class MasterIn(BaseModel):
    name: str
    code: Optional[str] = ''
    details: Optional[dict] = {}


class ProductIn(BaseModel):
    name: str
    brand_id: str
    model: str = ''
    capacity: str = ''
    product_type: str = 'battery'
    reorder_level: int = 10


class ItemIn(BaseModel):
    product_id: str
    quantity: int = Field(gt=0)


class TransactionIn(BaseModel):
    kind: str
    party_id: Optional[str] = None
    reference: str = ''
    notes: str = ''
    movement_date: Optional[str] = None  # YYYY-MM-DD picked by user
    items: list[ItemIn] = Field(min_length=1)


def now(): return datetime.now(timezone.utc).isoformat()


def clean(doc):
    if not doc:
        return None
    doc.pop('_id', None)
    return doc


async def seed():
    marker = await db.system.find_one({'_id': 'seeded'})
    if marker:
        return
    if os.environ.get('SEED_DEMO_DATA', 'false').lower() != 'true':
        # Production / fresh start — no demo data. Just drop the marker so we don't check again.
        await db.system.insert_one({'_id': 'seeded', 'at': now(), 'mode': 'empty'})
        return
    brands = [{'id': str(uuid.uuid4()), 'name': n, 'code': c, 'active': True}
              for n, c in [('Exide', 'EXD'), ('Massimo', 'MSM'), ('Microtek', 'MTK')]]
    await db.brands.insert_many(brands)
    products = []
    for b in brands:
        for cap in ['100Ah', '120Ah', '150Ah']:
            products.append({'id': str(uuid.uuid4()),
                             'name': f"{b['name']} {cap} Tubular",
                             'brand_id': b['id'],
                             'model': f"{b['code']}-{cap[:-2]}",
                             'capacity': cap,
                             'product_type': 'battery',
                             'reorder_level': 20,
                             'active': True})
        # Add one inverter per brand
        products.append({'id': str(uuid.uuid4()),
                         'name': f"{b['name']} 850VA Inverter",
                         'brand_id': b['id'],
                         'model': f"{b['code']}-INV850",
                         'capacity': '850VA',
                         'product_type': 'inverter',
                         'reorder_level': 5,
                         'active': True})
    # Add one trolley
    products.append({'id': str(uuid.uuid4()),
                     'name': f"{brands[0]['name']} Battery Trolley",
                     'brand_id': brands[0]['id'],
                     'model': f"{brands[0]['code']}-TRL",
                     'capacity': 'Standard',
                     'product_type': 'trolley',
                     'reorder_level': 3,
                     'active': True})
    await db.products.insert_many(products)
    await db.suppliers.insert_many([{'id': str(uuid.uuid4()), 'name': n, 'active': True}
                                    for n in ['Powerline Distributors', 'Reliable Energy Supply', 'North Star Batteries']])
    await db.dealers.insert_many([{'id': str(uuid.uuid4()), 'name': n, 'phone': p, 'city': c, 'active': True}
                                  for n, p, c in [('ABC Batteries', '9876543210', 'Pune'),
                                                  ('Shree Electricals', '9822012345', 'Mumbai'),
                                                  ('Kiran Power House', '9810012345', 'Nashik')]])
    for i, p in enumerate(products):
        qty = 35 + (i % 4) * 12 if p['product_type'] == 'battery' else (8 if p['product_type'] == 'inverter' else 4)
        await db.inventory.insert_one({'id': str(uuid.uuid4()), 'product_id': p['id'],
                                       'warehouse_id': MAIN_LOCATION,
                                       'available': qty,
                                       'inward': qty + 15,
                                       'outward': 15,
                                       'updated_at': now()})
    await db.system.insert_one({'_id': 'seeded', 'at': now()})


@api.post('/admin/reset')
async def reset_all():
    for col in ['brands', 'products', 'suppliers', 'dealers', 'inventory', 'transactions']:
        await db[col].delete_many({})
    await db.system.update_one({'_id': 'seeded'},
                                {'$set': {'at': now(), 'reset': True}},
                                upsert=True)
    return {'reset': True}


async def ensure_defaults():
    # Backfill product_type on existing products
    await db.products.update_many({'product_type': {'$exists': False}},
                                   {'$set': {'product_type': 'battery'}})


@app.on_event('startup')
async def startup():
    await seed()
    await ensure_defaults()


@api.get('/bootstrap')
async def bootstrap():
    out = {}
    for col in ['brands', 'products', 'suppliers', 'dealers']:
        docs = await db[col].find({'active': {'$ne': False}}, {'_id': 0}).to_list(2000)
        out[col] = [clean(x) for x in docs]
    return out


@api.get('/dashboard')
async def dashboard():
    inv = await db.inventory.find({}, {'_id': 0}).to_list(5000)
    tx = await db.transactions.find({}, {'_id': 0}).sort('created_at', -1).to_list(20)
    products = {x['id']: x for x in await db.products.find({'active': True}, {'_id': 0}).to_list(5000)}
    in_stock = out_of_stock = low_stock = 0
    for p in products.values():
        row = next((r for r in inv if r['product_id'] == p['id']), None)
        avail = row.get('available', 0) if row else 0
        reorder = p.get('reorder_level', 10)
        if avail <= 0:
            out_of_stock += 1
        elif avail <= reorder:
            low_stock += 1
            in_stock += 1
        else:
            in_stock += 1
    return {
        'available': sum(x.get('available', 0) for x in inv),
        'inward': sum(x.get('inward', 0) for x in inv),
        'outward': sum(x.get('outward', 0) for x in inv),
        'in_stock_models': in_stock,
        'out_of_stock_models': out_of_stock,
        'low_stock_models': low_stock,
        'total_models': len(products),
        'transactions': tx,
    }


@api.get('/stock')
async def stock():
    rows = await db.inventory.find({}, {'_id': 0}).to_list(5000)
    products = {x['id']: x for x in await db.products.find({}, {'_id': 0}).to_list(5000)}
    brands = {x['id']: x for x in await db.brands.find({}, {'_id': 0}).to_list(5000)}
    result = []
    for r in rows:
        p = products.get(r['product_id'], {})
        if not p or not p.get('active', True):
            continue
        b = brands.get(p.get('brand_id'), {})
        result.append({**r,
                       'product': p.get('name', 'Unknown'),
                       'product_id': p.get('id'),
                       'model': p.get('model', ''),
                       'capacity': p.get('capacity', ''),
                       'product_type': p.get('product_type', 'battery'),
                       'brand': b.get('name', 'Unknown'),
                       'brand_id': b.get('id'),
                       'reorder_level': p.get('reorder_level', 10),
                       'low': r.get('available', 0) <= p.get('reorder_level', 10)})
    return result


@api.post('/masters/{kind}')
async def create_master(kind: str, data: MasterIn):
    if kind not in ['brands', 'suppliers', 'dealers']:
        raise HTTPException(400, 'Only brands, suppliers and dealers are supported')
    doc = {'id': str(uuid.uuid4()), 'name': data.name.strip(), 'code': data.code,
           'active': True, 'created_at': now(), **data.details}
    await db[kind].insert_one(doc)
    return clean(doc)


@api.delete('/masters/{kind}/{item_id}')
async def delete_master(kind: str, item_id: str):
    if kind not in ['brands', 'suppliers', 'dealers']:
        raise HTTPException(400, 'Only brands, suppliers and dealers are supported')
    exists = await db[kind].find_one({'id': item_id})
    if not exists:
        raise HTTPException(404, f'{kind[:-1]} not found')
    if kind == 'brands':
        has_products = await db.products.find_one({'brand_id': item_id, 'active': {'$ne': False}})
        if has_products:
            await db.brands.update_one({'id': item_id}, {'$set': {'active': False}})
            return {'deactivated': True}
    else:
        has_tx = await db.transactions.find_one({'party_id': item_id})
        if has_tx:
            await db[kind].update_one({'id': item_id}, {'$set': {'active': False}})
            return {'deactivated': True}
    await db[kind].delete_one({'id': item_id})
    return {'deleted': True}


@api.post('/products')
async def create_product(data: ProductIn):
    if data.product_type not in PRODUCT_TYPES:
        raise HTTPException(400, 'Invalid product type')
    doc = {'id': str(uuid.uuid4()), **data.model_dump(), 'active': True, 'created_at': now()}
    await db.products.insert_one(doc)
    return clean(doc)


@api.delete('/products/{product_id}')
async def delete_product(product_id: str):
    exists = await db.products.find_one({'id': product_id})
    if not exists:
        raise HTTPException(404, 'Product not found')
    has_tx = await db.transactions.find_one({'items.product_id': product_id})
    if has_tx:
        # Preserve history — deactivate only
        await db.products.update_one({'id': product_id}, {'$set': {'active': False}})
        return {'deactivated': True}
    await db.products.delete_one({'id': product_id})
    await db.inventory.delete_many({'product_id': product_id})
    return {'deleted': True}


async def stock_change(item, kind, direction=1):
    delta = item['quantity'] * direction * (1 if kind == 'inward' else -1)
    counters = {'available': delta,
                'inward': item['quantity'] * direction if kind == 'inward' else 0,
                'outward': item['quantity'] * direction if kind == 'outward' else 0}
    await db.inventory.update_one(
        {'product_id': item['product_id'], 'warehouse_id': MAIN_LOCATION},
        {'$inc': counters, '$set': {'updated_at': now()}}, upsert=True)


async def reverse_transaction(doc):
    for item in doc.get('items', []):
        await stock_change(item, doc['kind'], -1)


@api.post('/transactions')
async def create_transaction(data: TransactionIn):
    if data.kind not in ['inward', 'outward']:
        raise HTTPException(400, 'Invalid transaction type')
    if data.kind == 'outward':
        for item in data.items:
            row = await db.inventory.find_one(
                {'product_id': item.product_id, 'warehouse_id': MAIN_LOCATION}, {'_id': 0})
            if not row or row.get('available', 0) < item.quantity:
                raise HTTPException(400, 'Not enough available stock')
    tid = f"{'INW' if data.kind == 'inward' else 'OUT'}-{(await db.transactions.count_documents({})) + 1:06d}"
    doc = {'id': str(uuid.uuid4()), 'transaction_id': tid, 'kind': data.kind,
           'party_id': data.party_id, 'reference': data.reference, 'notes': data.notes,
           'items': [x.model_dump() for x in data.items],
           'total_quantity': sum(x.quantity for x in data.items),
           'movement_date': data.movement_date or now()[:10],
           'created_at': now(), 'status': 'posted', 'edit_history': []}
    await db.transactions.insert_one(doc)
    for item in doc['items']:
        await stock_change(item, data.kind)
    return clean(doc)


@api.put('/transactions/{transaction_id}')
async def edit_transaction(transaction_id: str, data: TransactionIn):
    old = await db.transactions.find_one({'transaction_id': transaction_id}, {'_id': 0})
    if not old:
        raise HTTPException(404, 'Movement not found')
    await reverse_transaction(old)
    if data.kind == 'outward':
        for item in data.items:
            row = await db.inventory.find_one(
                {'product_id': item.product_id, 'warehouse_id': MAIN_LOCATION}, {'_id': 0})
            if not row or row.get('available', 0) < item.quantity:
                # Re-apply old effect so we don't corrupt stock
                for previous in old.get('items', []):
                    await stock_change(previous, old['kind'])
                raise HTTPException(400, 'Not enough available stock after correction')
    new_items = [x.model_dump() for x in data.items]
    history = old.get('edit_history', []) + [{'edited_at': now(),
                                               'old_items': old.get('items', []),
                                               'note': 'Posted movement corrected'}]
    updated = {**old, 'kind': data.kind, 'party_id': data.party_id,
               'reference': data.reference, 'notes': data.notes,
               'items': new_items,
               'total_quantity': sum(x['quantity'] for x in new_items),
               'movement_date': data.movement_date or old.get('movement_date') or old.get('created_at', now())[:10],
               'updated_at': now(), 'edit_history': history}
    await db.transactions.replace_one({'transaction_id': transaction_id}, updated)
    for item in new_items:
        await stock_change(item, data.kind)
    return clean(updated)


@api.get('/ledger')
async def ledger():
    tx = await db.transactions.find({}, {'_id': 0}).to_list(500)
    dealers = {x['id']: x for x in await db.dealers.find({}, {'_id': 0}).to_list(2000)}
    suppliers = {x['id']: x for x in await db.suppliers.find({}, {'_id': 0}).to_list(2000)}
    products = {x['id']: x for x in await db.products.find({}, {'_id': 0}).to_list(5000)}
    brands = {x['id']: x for x in await db.brands.find({}, {'_id': 0}).to_list(2000)}
    for row in tx:
        parties = dealers if row['kind'] == 'outward' else suppliers
        row['party_name'] = parties.get(row.get('party_id'), {}).get('name', '—')
        row['movement_date'] = row.get('movement_date') or (row.get('created_at', '')[:10])
        row['items_display'] = [{
            'product': products.get(i['product_id'], {}).get('name', 'Unknown'),
            'brand': brands.get(products.get(i['product_id'], {}).get('brand_id'), {}).get('name', ''),
            'product_type': products.get(i['product_id'], {}).get('product_type', 'battery'),
            'quantity': i['quantity'],
        } for i in row.get('items', [])]
    tx.sort(key=lambda r: (r.get('movement_date', ''), r.get('created_at', '')), reverse=True)
    return tx


@api.get('/dealers/{dealer_id}/profile')
async def dealer_profile(dealer_id: str):
    return await _party_profile(dealer_id, 'dealers', 'outward')


@api.get('/suppliers/{supplier_id}/profile')
async def supplier_profile(supplier_id: str):
    return await _party_profile(supplier_id, 'suppliers', 'inward')


async def _party_profile(party_id: str, collection: str, kind: str):
    party = await db[collection].find_one({'id': party_id}, {'_id': 0})
    if not party:
        raise HTTPException(404, f'{collection[:-1]} not found')
    tx = await db.transactions.find({'party_id': party_id, 'kind': kind}, {'_id': 0}).to_list(500)
    tx.sort(key=lambda r: (r.get('movement_date') or (r.get('created_at', '')[:10]), r.get('created_at', '')), reverse=True)
    products = {x['id']: x for x in await db.products.find({}, {'_id': 0}).to_list(5000)}
    brands = {x['id']: x for x in await db.brands.find({}, {'_id': 0}).to_list(2000)}
    history = []
    counts = {}
    total_units = 0
    for t in tx:
        for item in t.get('items', []):
            p = products.get(item['product_id'], {})
            brand = brands.get(p.get('brand_id'), {}).get('name', 'Unknown')
            qty = item['quantity']
            total_units += qty
            counts[brand] = counts.get(brand, 0) + qty
            history.append({'transaction_id': t['transaction_id'],
                            'date': t.get('movement_date') or (t.get('created_at', '')[:10]),
                            'brand': brand,
                            'model': p.get('name', 'Unknown'),
                            'product_type': p.get('product_type', 'battery'),
                            'quantity': qty,
                            'reference': t.get('reference', '')})
    key_label = 'DISPATCHED' if kind == 'outward' else 'RECEIVED'
    return {'party': party,
            'kind': kind,
            'key_label': key_label,
            'summary': {'total_units': total_units,
                        'total_orders': len(tx),
                        'top_brand': max(counts, key=counts.get) if counts else '—',
                        'last_transaction': history[0]['date'] if history else None},
            'history': history}


async def _party_profile_stub():
    return None


app.include_router(api)
app.add_middleware(CORSMiddleware, allow_credentials=True,
                   allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
                   allow_methods=['*'], allow_headers=['*'])


@app.on_event('shutdown')
async def shutdown():
    client.close()
