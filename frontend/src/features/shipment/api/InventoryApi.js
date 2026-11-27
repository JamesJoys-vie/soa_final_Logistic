import { BaseApi } from './BaseApi';

/** Reads Inventory's item catalogue to show names; Shipment only keeps item_id. */
export class InventoryApi extends BaseApi {
  constructor(http) {
    super(http, '/inventory');
  }

  listItems() {
    return this.request('get', '/items');
  }
}
