import { BaseApi } from './BaseApi';

/** The gateway forwards /api/shipment/* to the Shipment service. */
export class ShipmentApi extends BaseApi {
  constructor(http) {
    super(http, '/shipment');
  }

  listTrips(direction) {
    return this.request('get', '/trips', { params: { direction } });
  }

  listVehicles(status) {
    return this.request('get', '/vehicles', { params: { status } });
  }

  changeVehicleStatus(id, status) {
    return this.request('patch', `/vehicles/${id}/status`, { data: { status } });
  }

  listAssignments(status) {
    return this.request('get', '/assignments', { params: { status } });
  }

  createAssignment(assignment) {
    return this.request('post', '/assignments', { data: assignment });
  }

  confirm(id) {
    return this.request('post', `/assignments/${id}/confirm`);
  }

  reject(id) {
    return this.request('post', `/assignments/${id}/reject`);
  }

  withdraw(id) {
    return this.request('post', `/assignments/${id}/withdraw`);
  }
}
