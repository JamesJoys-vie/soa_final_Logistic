import { createContext, useContext, useMemo } from 'react';
import { InventoryApi } from '../api/InventoryApi';
import { ShipmentApi } from '../api/ShipmentApi';

const ShipmentContext = createContext(null);

/**
 * Provided by the shared app shell:
 *   http: axios instance with baseURL '/api' that attaches the JWT
 *   user: { id, role } of the signed-in user
 */
export function ShipmentProvider({ http, user, children }) {
  const value = useMemo(
    () => ({ shipment: new ShipmentApi(http), inventory: new InventoryApi(http), user }),
    [http, user],
  );
  return <ShipmentContext.Provider value={value}>{children}</ShipmentContext.Provider>;
}

export function useShipment() {
  const value = useContext(ShipmentContext);
  if (!value) throw new Error('Thiếu ShipmentProvider');
  return value;
}
